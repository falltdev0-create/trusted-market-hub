"""
app/api/routes/admin.py — لوحة الإدارة
مراجعة الإعلانات | قبول/رفض | إحصائيات
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.models.models import (
    Listing, ListingStatus, ListingVerification, User
)

router = APIRouter()


class ApproveIn(BaseModel):
    listing_id: str
    admin_id:   str


class RejectIn(BaseModel):
    listing_id: str
    admin_id:   str
    reason:     str


# ── Pending listings ──────────────────────────────────────────────────────────

@router.get("/pending-listings")
async def get_pending_listings(
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Listing)
        .where(Listing.status == ListingStatus.pending_review)
        .order_by(Listing.updated_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return [
        {
            "id":              str(l.id),
            "title":           l.title,
            "category":        l.category.value,
            "listing_type":    l.listing_type.value,
            "seller_id":       str(l.seller_id),
            "condition_grade": l.condition_grade.value if l.condition_grade else None,
            "condition_score": l.condition_score,
            "price":           l.price,
            "price_max_limit": l.price_max_limit,
            "city":            l.city,
            "created_at":      l.created_at.isoformat(),
        }
        for l in rows
    ]


@router.get("/listing/{listing_id}/full-review")
async def get_listing_full_review(listing_id: str, db: AsyncSession = Depends(get_db)):
    """تفاصيل الإعلان الكاملة للمراجعة (صور + وثائق + نتيجة AI)"""
    listing = (await db.execute(
<<<<<<< HEAD
        select(Listing).where(Listing.id == listing_id)
=======
        select(Listing).where(Listing.id == uuid.UUID(listing_id))
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)

    verif = (await db.execute(
<<<<<<< HEAD
        select(ListingVerification).where(ListingVerification.listing_id == listing_id)
=======
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(listing_id))
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
    )).scalar_one_or_none()

    return {
        "listing": {
            "id":               str(listing.id),
            "title":            listing.title,
            "category":         listing.category.value,
            "listing_type":     listing.listing_type.value,
            "status":           listing.status.value,
            "condition_grade":  listing.condition_grade.value if listing.condition_grade else None,
            "condition_score":  listing.condition_score,
            "condition_report": listing.condition_report,
            "price":            listing.price,
            "price_max_limit":  listing.price_max_limit,
            "currency":         listing.currency,
            "details":          listing.details,
            "images":           [{"url": img.url, "type": img.image_type} for img in listing.images],
        },
        "verification": {
            "id_doc_url":       verif.owner_id_doc_url  if verif else None,
            "ownership_doc_url": verif.ownership_doc_url if verif else None,
            "match_score":      verif.match_score        if verif else None,
            "match_status":     verif.match_status.value if verif else None,
            "match_details":    verif.match_details      if verif else None,
        } if verif else None,
    }


# ── Approve / Reject ──────────────────────────────────────────────────────────

@router.post("/approve-listing")
async def approve_listing(body: ApproveIn, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(
<<<<<<< HEAD
        select(Listing).where(Listing.id == body.listing_id)
=======
        select(Listing).where(Listing.id == uuid.UUID(body.listing_id))
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)
    if listing.status != ListingStatus.pending_review:
        raise HTTPException(400, "الإعلان ليس في حالة انتظار المراجعة")

    listing.status       = ListingStatus.published
    listing.published_at = datetime.utcnow()
    await db.commit()
    return {"status": "published", "listing_id": body.listing_id}


@router.post("/reject-listing")
async def reject_listing(body: RejectIn, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(
<<<<<<< HEAD
        select(Listing).where(Listing.id == body.listing_id)
=======
        select(Listing).where(Listing.id == uuid.UUID(body.listing_id))
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)

    listing.status          = ListingStatus.rejected
    listing.rejected_reason = body.reason

    verif = (await db.execute(
<<<<<<< HEAD
        select(ListingVerification).where(ListingVerification.listing_id == body.listing_id)
    )).scalar_one_or_none()
    if verif:
        verif.rejection_reason = body.reason
        verif.reviewed_by      = body.admin_id
=======
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(body.listing_id))
    )).scalar_one_or_none()
    if verif:
        verif.rejection_reason = body.reason
        verif.reviewed_by      = uuid.UUID(body.admin_id)
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
        verif.reviewed_at      = datetime.utcnow()

    await db.commit()
    return {"status": "rejected", "reason": body.reason}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/dashboard-stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    async def _count(status: ListingStatus) -> int:
        r = await db.execute(
            select(func.count()).select_from(Listing).where(Listing.status == status)
        )
        return r.scalar()

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()

    return {
        "total_users":    total_users,
        "pending_review": await _count(ListingStatus.pending_review),
        "published":      await _count(ListingStatus.published),
        "rejected":       await _count(ListingStatus.rejected),
        "sold":           await _count(ListingStatus.sold),
    }
