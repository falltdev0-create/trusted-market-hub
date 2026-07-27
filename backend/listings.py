"""
Listings Routes — مسارات الإعلانات
Full lifecycle: draft → images → AI condition → docs → AI match → price → publish
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.listing import (
    Listing, ListingImage, ListingVerification,
    ListingCategory, ListingType, ListingStatus, ConditionGrade
)
from pydantic import BaseModel

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class CreateListingRequest(BaseModel):
    category: ListingCategory
    listing_type: ListingType
    title: str
    description: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None


class SetPriceRequest(BaseModel):
    price: float


class UpdateDetailsRequest(BaseModel):
    details: dict


class ListingResponse(BaseModel):
    id: str
    category: str
    listing_type: str
    title: str
    description: Optional[str]
    status: str
    price: Optional[float]
    price_max_limit: Optional[float]
    condition_grade: Optional[str]
    condition_score: Optional[float]
    city: Optional[str]
    district: Optional[str]
    images: List[dict]
    seller_name: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


# ── Helper ───────────────────────────────────────────────────────────────────

def get_price_limit(category: str, listing_type: str, condition: str) -> float:
    try:
        return settings.PRICE_LIMITS[category][listing_type][condition]
    except KeyError:
        return 9_999_999


def listing_to_dict(listing: Listing) -> dict:
    return {
        "id": str(listing.id),
        "category": listing.category.value,
        "listing_type": listing.listing_type.value,
        "title": listing.title,
        "description": listing.description,
        "status": listing.status.value,
        "price": listing.price,
        "price_max_limit": listing.price_max_limit,
        "condition_grade": listing.condition_grade.value if listing.condition_grade else None,
        "condition_score": listing.condition_score,
        "city": listing.city,
        "district": listing.district,
        "images": [{"url": img.url, "type": img.image_type, "order": img.order}
                   for img in (listing.images or [])],
        "seller_name": listing.seller.full_name if listing.seller else None,
        "created_at": listing.created_at.isoformat(),
        "details": listing.details,
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
async def create_listing(
    body: CreateListingRequest,
    seller_id: str = Query(..., description="JWT user id"),
    db: AsyncSession = Depends(get_db),
):
    """إنشاء إعلان جديد (مسودة)"""
    listing = Listing(
        id=uuid.uuid4(),
        seller_id=uuid.UUID(seller_id),
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
    await db.refresh(listing)
    return {"listing_id": str(listing.id), "status": "draft"}


@router.post("/{listing_id}/set-condition")
async def set_condition_result(
    listing_id: str,
    grade: ConditionGrade,
    score: float,
    report: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    يُستدعى بعد تحليل نموذج AI لتقييم حالة السلعة.
    يحدّث الإعلان بنتيجة التقييم ويحسب الحد السعري الأقصى.
    """
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing.condition_grade = grade
    listing.condition_score = score
    listing.condition_report = report
    listing.price_max_limit = get_price_limit(
        listing.category.value, listing.listing_type.value, grade.value
    )
    listing.status = ListingStatus.condition_assessed
    await db.commit()

    return {
        "condition_grade": grade.value,
        "condition_score": score,
        "price_max_limit": listing.price_max_limit,
        "currency": listing.currency,
    }


@router.post("/{listing_id}/set-price")
async def set_price(
    listing_id: str,
    body: SetPriceRequest,
    db: AsyncSession = Depends(get_db),
):
    """تحديد سعر الإعلان (لا يتجاوز الحد الأقصى)"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.status not in [ListingStatus.docs_verified]:
        raise HTTPException(
            status_code=400,
            detail="يجب إتمام التحقق من الوثائق أولاً قبل تحديد السعر"
        )

    if listing.price_max_limit and body.price > listing.price_max_limit:
        raise HTTPException(
            status_code=422,
            detail=f"السعر المدخل يتجاوز الحد الأقصى المسموح ({listing.price_max_limit:,.0f} {listing.currency})"
        )

    listing.price = body.price
    listing.status = ListingStatus.price_set
    await db.commit()

    return {"price": body.price, "status": "price_set"}


@router.post("/{listing_id}/submit-for-review")
async def submit_for_review(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """رفع الإعلان للمراجعة النهائية من الإدارة"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.status != ListingStatus.price_set:
        raise HTTPException(
            status_code=400,
            detail="يجب اكتمال جميع الخطوات قبل الرفع للمراجعة"
        )

    listing.status = ListingStatus.pending_review
    await db.commit()

    return {"status": "pending_review", "message": "تم إرسال الإعلان للمراجعة"}


@router.post("/{listing_id}/update-details")
async def update_details(
    listing_id: str,
    body: UpdateDetailsRequest,
    db: AsyncSession = Depends(get_db),
):
    """تحديث البيانات الإضافية (مساحة، سنة الصنع، عدد الغرف، إلخ)"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    listing.details = body.details
    await db.commit()
    return {"status": "updated"}


@router.get("/")
async def get_listings(
    category: Optional[ListingCategory] = None,
    listing_type: Optional[ListingType] = None,
    condition: Optional[ConditionGrade] = None,
    city: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """عرض الإعلانات المنشورة في المعرض"""
    filters = [Listing.status == ListingStatus.published]
    if category:
        filters.append(Listing.category == category)
    if listing_type:
        filters.append(Listing.listing_type == listing_type)
    if condition:
        filters.append(Listing.condition_grade == condition)
    if city:
        filters.append(Listing.city.ilike(f"%{city}%"))
    if min_price is not None:
        filters.append(Listing.price >= min_price)
    if max_price is not None:
        filters.append(Listing.price <= max_price)

    total_result = await db.execute(
        select(func.count()).select_from(Listing).where(and_(*filters))
    )
    total = total_result.scalar()

    result = await db.execute(
        select(Listing)
        .where(and_(*filters))
        .order_by(Listing.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    listings = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [listing_to_dict(l) for l in listings],
    }


@router.get("/{listing_id}")
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    """تفاصيل إعلان واحد"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing_to_dict(listing)
