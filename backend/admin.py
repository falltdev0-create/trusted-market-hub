"""
Admin Routes — لوحة الإدارة
مراجعة الطلبات، نشر/رفض الإعلانات، إدارة المستخدمين
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
from typing import Optional
import uuid

from app.core.database import get_db
from app.models.listing import (
    Listing, ListingStatus, ListingVerification,
    VerificationStatus, User
)
from pydantic import BaseModel

router = APIRouter()


class ApproveRequest(BaseModel):
    listing_id: str
    admin_id: str


class RejectRequest(BaseModel):
    listing_id: str
    admin_id: str
    reason: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/pending-listings")
async def get_pending_listings(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """قائمة الإعلانات بانتظار المراجعة"""
    result = await db.execute(
        select(Listing)
        .where(Listing.status == ListingStatus.pending_review)
        .order_by(Listing.updated_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    listings = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "title": l.title,
            "category": l.category.value,
            "listing_type": l.listing_type.value,
            "seller_id": str(l.seller_id),
            "condition_grade": l.condition_grade.value if l.condition_grade else None,
            "price": l.price,
            "price_max_limit": l.price_max_limit,
            "created_at": l.created_at.isoformat(),
            "city": l.city,
        }
        for l in listings
    ]


@router.get("/listing/{listing_id}/full-review")
async def get_listing_full_review(listing_id: str, db: AsyncSession = Depends(get_db)):
    """تفاصيل كاملة للإعلان للمراجعة (صور + وثائق + نتيجة AI)"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404)

    verif_result = await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(listing_id))
    )
    verif = verif_result.scalar_one_or_none()

    return {
        "listing": {
            "id": str(listing.id),
            "title": listing.title,
            "category": listing.category.value,
            "listing_type": listing.listing_type.value,
            "status": listing.status.value,
            "condition_grade": listing.condition_grade.value if listing.condition_grade else None,
            "condition_score": listing.condition_score,
            "condition_report": listing.condition_report,
            "price": listing.price,
            "price_max_limit": listing.price_max_limit,
            "images": [{"url": img.url, "type": img.image_type} for img in listing.images],
            "details": listing.details,
        },
        "verification": {
            "id_doc_url": verif.owner_id_doc_url if verif else None,
            "ownership_doc_url": verif.ownership_doc_url if verif else None,
            "match_score": verif.match_score if verif else None,
            "match_status": verif.match_status.value if verif else None,
            "match_details": verif.match_details if verif else None,
        } if verif else None,
    }


@router.post("/approve-listing")
async def approve_listing(body: ApproveRequest, db: AsyncSession = Depends(get_db)):
    """قبول الإعلان ونشره في المعرض"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(body.listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404)

    if listing.status != ListingStatus.pending_review:
        raise HTTPException(status_code=400, detail="الإعلان ليس في حالة انتظار المراجعة")

    listing.status = ListingStatus.published
    listing.published_at = datetime.utcnow()
    await db.commit()

    return {"status": "published", "listing_id": body.listing_id}


@router.post("/reject-listing")
async def reject_listing(body: RejectRequest, db: AsyncSession = Depends(get_db)):
    """رفض الإعلان مع ذكر السبب"""
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(body.listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404)

    listing.status = ListingStatus.rejected

    # Save rejection reason in verification record
    verif_result = await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(body.listing_id))
    )
    verif = verif_result.scalar_one_or_none()
    if verif:
        verif.rejection_reason = body.reason
        verif.reviewed_by = uuid.UUID(body.admin_id)
        verif.reviewed_at = datetime.utcnow()

    await db.commit()
    return {"status": "rejected", "reason": body.reason}


@router.get("/dashboard-stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """إحصائيات لوحة التحكم"""
    async def count_by_status(status: ListingStatus):
        r = await db.execute(
            select(func.count()).select_from(Listing).where(Listing.status == status)
        )
        return r.scalar()

    total_users_r = await db.execute(select(func.count()).select_from(User))
    total_users   = total_users_r.scalar()

    return {
        "total_users": total_users,
        "pending_review": await count_by_status(ListingStatus.pending_review),
        "published": await count_by_status(ListingStatus.published),
        "rejected": await count_by_status(ListingStatus.rejected),
        "sold": await count_by_status(ListingStatus.sold),
    }
