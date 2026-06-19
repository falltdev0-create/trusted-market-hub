"""
app/api/routes/search.py — البحث في الإعلانات
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import Optional

from app.core.database import get_db
from app.models.models import Listing, ListingStatus

router = APIRouter()


@router.get("/")
async def search(
    q:            Optional[str]   = Query(None, description="نص البحث"),
    category:     Optional[str]   = None,
    listing_type: Optional[str]   = None,
    city:         Optional[str]   = None,
    condition:    Optional[str]   = None,
    min_price:    Optional[float] = None,
    max_price:    Optional[float] = None,
    page:         int = Query(1, ge=1),
    page_size:    int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    filters = [Listing.status == ListingStatus.published]

    if q:
        filters.append(or_(
            Listing.title.ilike(f"%{q}%"),
            Listing.description.ilike(f"%{q}%"),
            Listing.city.ilike(f"%{q}%"),
        ))
    if category:     filters.append(Listing.category     == category)
    if listing_type: filters.append(Listing.listing_type == listing_type)
    if city:         filters.append(Listing.city.ilike(f"%{city}%"))
    if condition:    filters.append(Listing.condition_grade == condition)
    if min_price:    filters.append(Listing.price >= min_price)
    if max_price:    filters.append(Listing.price <= max_price)

    rows = (await db.execute(
        select(Listing)
        .where(and_(*filters))
        .order_by(Listing.published_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return {
        "results": [
            {
                "id":              str(l.id),
                "title":           l.title,
                "category":        l.category.value,
                "listing_type":    l.listing_type.value,
                "price":           l.price,
                "city":            l.city,
                "condition_grade": l.condition_grade.value if l.condition_grade else None,
                "cover_image":     l.images[0].url if l.images else None,
            }
            for l in rows
        ]
    }
