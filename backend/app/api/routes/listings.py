"""
app/api/routes/listings.py — مسارات الإعلانات المتكاملة
تدعم واجهة React الحالية: إنشاء مسودة، تحديث التفاصيل، السعر الحر، التصنيف السعري، المراجعة، وإعلاناتي.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.models.models import (
    Listing,
    ListingCategory,
    ListingStatus,
    ListingType,
    Notification,
    User,
)
from app.services.ai_service import get_ai_service

router = APIRouter()


async def _get_owned(listing_id: str, current_user: User, db: AsyncSession) -> Listing:
    """404 عندما لا يوجد الإعلان، و403 فقط عند محاولة الوصول لإعلان مستخدم آخر."""
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود أو انتهت جلسة الإنشاء، ابدأ إعلاناً جديداً")
    role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if str(listing.seller_id) != str(current_user.id) and role not in ("admin", "super_admin"):
        raise HTTPException(403, "غير مصرح لك بتعديل هذا الإعلان")
    return listing



class ListingCreateIn(BaseModel):
    kind: Optional[str] = None
    category: Optional[str] = None
    listing_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None


class DetailsIn(BaseModel):
    details: dict[str, Any]


class PriceIn(BaseModel):
    price: float


def _normalize_category(value: Optional[str]) -> ListingCategory:
    if value in ("property", "real_estate", "house", None):
        return ListingCategory.house
    if value == "car":
        return ListingCategory.car
    raise HTTPException(400, "فئة الإعلان غير صحيحة")


def _normalize_type(value: Optional[str]) -> ListingType:
    if value in ("sale", None):
        return ListingType.sale
    if value == "rent":
        return ListingType.rent
    raise HTTPException(400, "نوع الإعلان غير صحيح")


def _category_for_client(category: ListingCategory) -> str:
    return "property" if category == ListingCategory.house else category.value


def _cover(listing: Listing) -> Optional[str]:
    return listing.images[0].url if listing.images else None


def _to_listing_row(listing: Listing) -> dict[str, Any]:
    return {
        "id": str(listing.id),
        "title": listing.title,
        "description": listing.description,
        "category": _category_for_client(listing.category),
        "backend_category": listing.category.value,
        "listing_type": listing.listing_type.value,
        "status": listing.status.value,
        "price": listing.price,
        "price_tier": listing.price_tier,
        "suggested_min": listing.suggested_min,
        "suggested_max": listing.suggested_max,
        "currency": listing.currency,
        "city": listing.city,
        "district": listing.district,
        "condition_grade": listing.condition_grade.value if listing.condition_grade else None,
        "condition_score": listing.condition_score,
        "details": listing.details,
        "view_count": listing.view_count,
        "cover_image": _cover(listing),
        "images": [{"url": img.url, "type": img.image_type} for img in (listing.images or [])],
        "seller_id": str(listing.seller_id),
        "published_at": listing.published_at.isoformat() if listing.published_at else None,
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
    }


@router.post("/")
async def create_listing_from_body(
    body: ListingCreateIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    category = _normalize_category(body.category)
    listing_type = _normalize_type(body.listing_type)
    title = body.title or ("إعلان عقار" if category == ListingCategory.house else "إعلان سيارة")

    listing = Listing(
        id=str(uuid.uuid4()),
        seller_id=str(current_user.id),
        category=category,
        listing_type=listing_type,
        title=title,
        description=body.description,
        city=body.city,
        district=body.district,
        status=ListingStatus.draft,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return {"id": str(listing.id), "listing": _to_listing_row(listing), "status": listing.status.value}


@router.post("/create")
async def create_listing_legacy(
    category: str,
    listing_type: str,
    title: str,
    description: Optional[str] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await create_listing_from_body(
        ListingCreateIn(
            category=category,
            listing_type=listing_type,
            title=title,
            description=description,
            city=city,
            district=district,
        ),
        current_user,
        db,
    )


@router.get("/mine")
async def my_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Listing)
        .where(Listing.seller_id == str(current_user.id))
        .order_by(desc(Listing.updated_at))
        .limit(100)
    )).scalars().all()
    return [_to_listing_row(l) for l in rows]


@router.get("/")
async def list_listings(
    category: Optional[str] = None,
    listing_type: Optional[str] = None,
    city: Optional[str] = None,
    price_tier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    query = select(Listing).where(Listing.status == ListingStatus.published)
    if category:
        query = query.where(Listing.category == _normalize_category(category))
    if listing_type:
        query = query.where(Listing.listing_type == _normalize_type(listing_type))
    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if price_tier in {"cheap", "medium", "expensive"}:
        query = query.where(Listing.price_tier == price_tier)
    if min_price is not None:
        query = query.where(Listing.price >= min_price)
    if max_price is not None:
        query = query.where(Listing.price <= max_price)

    rows = (await db.execute(
        query.order_by(desc(Listing.published_at), desc(Listing.created_at)).offset(skip).limit(limit)
    )).scalars().all()
    return [_to_listing_row(l) for l in rows]


@router.get("/{listing_id}")
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(select(Listing).where(Listing.id == listing_id))).scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")
    listing.view_count = (listing.view_count or 0) + 1
    await db.commit()
    return _to_listing_row(listing)


@router.post("/{listing_id}/update-details")
async def update_details(
    listing_id: str,
    body: DetailsIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned(listing_id, current_user, db)

    details = body.details or {}
    listing.details = details
    listing.title = details.get("title") or listing.title
    listing.description = details.get("description") or listing.description
    listing.city = details.get("city") or listing.city
    listing.district = details.get("district") or details.get("area") or listing.district
    await db.commit()
    return {"ok": True, "listing": _to_listing_row(listing)}


@router.get("/{listing_id}/price-estimate")
async def price_estimate(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned(listing_id, current_user, db)
    ai = get_ai_service()
    result = await ai.estimate_price(
        category=listing.category.value,
        listing_type=listing.listing_type.value,
        condition_grade=listing.condition_grade.value if listing.condition_grade else "good",
        features=listing.details or {},
    )
    listing.suggested_min = float(result.get("suggested_min") or 0)
    listing.suggested_max = float(result.get("suggested_max") or 0)
    if listing.price:
        listing.price_tier = ai.classify_tier(float(listing.price), listing.category.value)
    await db.commit()
    return {
        "suggested_min": listing.suggested_min,
        "suggested_max": listing.suggested_max,
        "market_avg": result.get("market_avg"),
        "tier": result.get("tier"),
        "confidence": result.get("confidence", 0.6),
    }


@router.post("/{listing_id}/set-price")
async def set_price(
    listing_id: str,
    body: PriceIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned(listing_id, current_user, db)
    if body.price <= 0:
        raise HTTPException(400, "أدخل سعراً صحيحاً")

    ai = get_ai_service()
    listing.price = body.price
    listing.price_tier = ai.classify_tier(float(body.price), listing.category.value)
    listing.status = ListingStatus.price_set
    await db.commit()
    return {"price": listing.price, "price_tier": listing.price_tier, "status": listing.status.value}


@router.post("/{listing_id}/submit-for-review")
async def submit_for_review(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned(listing_id, current_user, db)
    if not listing.price:
        raise HTTPException(400, "يجب تحديد السعر قبل إرسال الإعلان")
    listing.status = ListingStatus.pending_review
    db.add(Notification(
        id=str(uuid.uuid4()),
        user_id=str(current_user.id),
        type="listing_submitted",
        title="تم إرسال إعلانك للمراجعة",
        body=listing.title,
        is_read=False,
    ))
    await db.commit()
    return {"status": listing.status.value, "listing_id": str(listing.id)}


@router.post("/{listing_id}/publish")
async def publish_listing(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    listing = await _get_owned(listing_id, current_user, db)
    if listing.status not in [ListingStatus.price_set, ListingStatus.pending_review]:
        raise HTTPException(400, f"لا يمكن نشر الإعلان من حالة {listing.status.value}")
    listing.status = ListingStatus.published
    listing.published_at = datetime.utcnow()
    await db.commit()
    return {"status": listing.status.value, "published_at": listing.published_at.isoformat()}