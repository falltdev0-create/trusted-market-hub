"""
app/api/routes/listings.py — مسارات الإعلانات
دورة الحياة: مسودة ← صور+AI ← وثائق ← سعر ← مراجعة ← نشر
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, or_
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.models import (
    Listing, ListingImage, ListingCategory,
    ListingType, ListingStatus, ConditionGrade, User
)
from app.api.routes.auth import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateListingIn(BaseModel):
    category:     ListingCategory
    listing_type: ListingType
    title:        str
    description:  Optional[str] = None
    city:         Optional[str] = None
    district:     Optional[str] = None


class SetPriceIn(BaseModel):
    price: float


class UpdateDetailsIn(BaseModel):
    details: dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_price_limit(category: str, listing_type: str, condition: str) -> float:
    try:
        return settings.PRICE_CAPS[category][listing_type][condition]
    except KeyError:
        return 99_999_999


def _serialize(l: Listing) -> dict:
    return {
        "id":               str(l.id),
        "category":         l.category.value,
        "listing_type":     l.listing_type.value,
        "title":            l.title,
        "description":      l.description,
        "status":           l.status.value,
        "city":             l.city,
        "district":         l.district,
        "price":            l.price,
        "price_max_limit":  l.price_max_limit,
        "currency":         l.currency,
        "condition_grade":  l.condition_grade.value if l.condition_grade else None,
        "condition_score":  l.condition_score,
        "condition_report": l.condition_report,
        "details":          l.details,
        "images":           [{"url": i.url, "type": i.image_type, "order": i.order}
                             for i in (l.images or [])],
        "seller_name":      l.seller.full_name if l.seller else None,
        "seller_id":        str(l.seller_id),
        "view_count":       l.view_count,
        "published_at":     l.published_at.isoformat() if l.published_at else None,
        "created_at":       l.created_at.isoformat(),
    }


async def _get_or_404(listing_id: str, db: AsyncSession) -> Listing:
    result  = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")
    return listing


# ── Step 1: Create draft ──────────────────────────────────────────────────────

@router.post("/", status_code=201)
async def create_listing(
    body: CreateListingIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=current_user.id,
        category=body.category,
        listing_type=body.listing_type,
        title=body.title,
        description=body.description,
        city=body.city,
        district=body.district,
        status=ListingStatus.draft,
    )
    db.add(listing)
    await db.commit()
    return {"listing_id": str(listing.id), "status": "draft"}


# ── Step 2: Receive condition result from upload route ────────────────────────

@router.post("/{listing_id}/set-condition")
async def set_condition(
    listing_id: str,
    grade: ConditionGrade,
    score: float,
    report: dict,
    db: AsyncSession = Depends(get_db),
):
    """يُستدعى داخلياً من upload route بعد تحليل AI."""
    listing = await _get_or_404(listing_id, db)
    listing.condition_grade  = grade
    listing.condition_score  = score
    listing.condition_report = report
    listing.price_max_limit  = get_price_limit(
        listing.category.value, listing.listing_type.value, grade.value
    )
    listing.status = ListingStatus.condition_assessed
    await db.commit()
    return {
        "condition_grade": grade.value,
        "condition_score": score,
        "price_max_limit": listing.price_max_limit,
        "currency":        listing.currency,
    }


# ── Step 3: Update extra details ──────────────────────────────────────────────

@router.patch("/{listing_id}/details")
async def update_details(
    listing_id: str,
    body: UpdateDetailsIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_or_404(listing_id, db)
    if str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    listing.details = body.details
    await db.commit()
    return {"status": "updated"}


# ── Step 4: Set price ─────────────────────────────────────────────────────────

@router.post("/{listing_id}/set-price")
async def set_price(
    listing_id: str,
    body: SetPriceIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_or_404(listing_id, db)
    if str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")

    if listing.status != ListingStatus.docs_verified:
        raise HTTPException(400, "يجب إتمام التحقق من الوثائق أولاً")

    if listing.price_max_limit and body.price > listing.price_max_limit:
        raise HTTPException(
            422,
            f"السعر يتجاوز الحد الأقصى ({listing.price_max_limit:,.0f} {listing.currency})"
        )

    listing.price  = body.price
    listing.status = ListingStatus.price_set
    await db.commit()
    return {"price": body.price, "status": "price_set"}


# ── Step 5: Submit for admin review ──────────────────────────────────────────

@router.post("/{listing_id}/submit")
async def submit_for_review(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_or_404(listing_id, db)
    if str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    if listing.status != ListingStatus.price_set:
        raise HTTPException(400, "يجب اكتمال جميع الخطوات")

    listing.status = ListingStatus.pending_review
    await db.commit()
    return {"status": "pending_review", "message": "تم إرسال الإعلان للمراجعة ✅"}


# ── Public: Browse ────────────────────────────────────────────────────────────

@router.get("/")
async def get_listings(
    category:     Optional[ListingCategory] = None,
    listing_type: Optional[ListingType]     = None,
    condition:    Optional[ConditionGrade]  = None,
    city:         Optional[str]  = Query(None),
    q:            Optional[str]  = Query(None),
    min_price:    Optional[float] = None,
    max_price:    Optional[float] = None,
    page:         int = Query(1, ge=1),
    page_size:    int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = [Listing.status == ListingStatus.published]
    if category:     filters.append(Listing.category == category)
    if listing_type: filters.append(Listing.listing_type == listing_type)
    if condition:    filters.append(Listing.condition_grade == condition)
    if city:         filters.append(Listing.city.ilike(f"%{city}%"))
    if min_price:    filters.append(Listing.price >= min_price)
    if max_price:    filters.append(Listing.price <= max_price)
    if q:
        filters.append(or_(
            Listing.title.ilike(f"%{q}%"),
            Listing.description.ilike(f"%{q}%"),
        ))

    total = (await db.execute(
        select(func.count()).select_from(Listing).where(and_(*filters))
    )).scalar()

    rows = (await db.execute(
        select(Listing)
        .where(and_(*filters))
        .order_by(Listing.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {
        "total":     total,
        "page":      page,
        "page_size": page_size,
        "pages":     (total + page_size - 1) // page_size,
        "items":     [_serialize(l) for l in rows],
    }


@router.get("/my")
async def get_my_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """إعلاناتي الخاصة بجميع الحالات"""
    rows = (await db.execute(
        select(Listing)
        .where(Listing.seller_id == current_user.id)
        .order_by(Listing.created_at.desc())
    )).scalars().all()
    return [_serialize(l) for l in rows]


@router.get("/{listing_id}")
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    listing = await _get_or_404(listing_id, db)
    if listing.status != ListingStatus.published:
        raise HTTPException(404, "الإعلان غير متاح")
    listing.view_count = (listing.view_count or 0) + 1
    await db.commit()
    return _serialize(listing)
