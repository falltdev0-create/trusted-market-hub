"""
app/api/routes/users.py — مسارات المستخدمين
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import get_user_admin_role
from app.models.models import User
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """بيانات المستخدم الحالي"""
    admin_role = await get_user_admin_role(current_user, db)
    return {
        "id":          str(current_user.id),
        "email":       current_user.email,
        "full_name":   current_user.full_name,
        "phone":       current_user.phone,
        "kyc_status":  current_user.kyc_status.value,
        "is_verified": current_user.is_verified,
        "avatar_url":  current_user.avatar_url,
        "role":        "admin" if admin_role else current_user.role.value,
        "admin_role":  admin_role,
    }


@router.get("/{user_id}/listings")
async def get_user_listings(
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """إعلانات مستخدم معين"""
    from app.models.models import Listing, ListingStatus
    result = await db.execute(
        select(Listing)
        .where(
            Listing.seller_id == user_id,
            Listing.status == ListingStatus.published,
        )
        .order_by(Listing.published_at.desc())
        .limit(50)
    )
    listings = result.scalars().all()
    return [
        {
            "id":              str(l.id),
            "title":           l.title,
            "category":        l.category.value,
            "listing_type":    l.listing_type.value,
            "price":           l.price,
            "condition_grade": l.condition_grade.value if l.condition_grade else None,
            "city":            l.city,
            "published_at":    l.published_at.isoformat() if l.published_at else None,
            "cover_image":     l.images[0].url if l.images else None,
        }
        for l in listings
    ]
