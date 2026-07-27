"""
<<<<<<< HEAD
app/api/routes/listings.py — مسارات الإعلانات الكاملة
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
import uuid
import json
from datetime import datetime

from app.core.database import get_db
from app.models.models import (
    Listing, ListingImage, ListingStatus, ListingCategory, 
    ListingType, ConditionGrade, ListingVerification
)
from app.api.routes.auth import get_current_user
from app.models.models import User
from app.services.ai_service import get_ai_service
from app.services.storage_service import get_storage_service
=======
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
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b

router = APIRouter()


<<<<<<< HEAD
# ══════════════════════════════════════════════════════════════════════════
# Create Listing
# ══════════════════════════════════════════════════════════════════════════

@router.post("/create")
async def create_listing(
    category: str,
    listing_type: str,
    title: str,
    description: Optional[str] = None,
    city: Optional[str] = None,
    district: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """إنشاء إعلان جديد"""
    try:
        # التحقق من الفئة والنوع
        category_enum = ListingCategory[category]
        type_enum = ListingType[listing_type]
    except KeyError:
        raise HTTPException(400, "فئة أو نوع غير صحيح")
    
    listing = Listing(
        id=str(uuid.uuid4()),
        seller_id=str(current_user.id),
        category=category_enum,
        listing_type=type_enum,
        title=title,
        description=description,
        city=city,
        district=district,
        status=ListingStatus.draft,
    )
    
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    
    return {
        "id": listing.id,
        "status": listing.status.value,
        "message": "تم إنشاء الإعلان بنجاح",
    }


# ══════════════════════════════════════════════════════════════════════════
# Upload Images & Assess Condition
# ══════════════════════════════════════════════════════════════════════════

@router.post("/{listing_id}/upload-images")
async def upload_images(
    listing_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """رفع الصور وتقييم الحالة تلقائيا"""
    # التحقق من الإعلان
    listing = await db.get(Listing, listing_id)
    if not listing or str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    
    storage = get_storage_service()
    ai = get_ai_service()
    
    uploaded_images = []
    for idx, file in enumerate(files):
        # رفع الملف
        url = await storage.upload_file(file, f"listings/{listing_id}")
        
        image = ListingImage(
            id=str(uuid.uuid4()),
            listing_id=listing_id,
            url=url,
            order=idx,
            image_type="item",
        )
        db.add(image)
        uploaded_images.append(url)
    
    # تقييم الحالة من الصورة الأولى
    if uploaded_images:
        condition_result = await ai.assess_condition(
            uploaded_images[0],
            category=listing.category.value
        )
        listing.condition_grade = ConditionGrade[condition_result.get("grade", "good")]
        listing.condition_score = condition_result.get("score", 0.5)
        listing.condition_report = condition_result
        listing.status = ListingStatus.condition_assessed
    
    await db.commit()
    
    return {
        "uploaded": len(uploaded_images),
        "condition": listing.condition_report,
        "status": listing.status.value,
    }


# ══════════════════════════════════════════════════════════════════════════
# Upload Documents & Verify
# ══════════════════════════════════════════════════════════════════════════

@router.post("/{listing_id}/upload-documents")
async def upload_documents(
    listing_id: str,
    owner_doc: UploadFile = File(...),
    ownership_doc: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """رفع المستندات والتحقق منها"""
    listing = await db.get(Listing, listing_id)
    if not listing or str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    
    storage = get_storage_service()
    ai = get_ai_service()
    
    # رفع المستندات
    owner_url = await storage.upload_file(owner_doc, f"listings/{listing_id}/docs")
    ownership_url = await storage.upload_file(ownership_doc, f"listings/{listing_id}/docs")
    
    # التحقق من المستندات
    verify_result = await ai.verify_document(owner_url, "owner_id")
    
    # حفظ التحقق
    verification = ListingVerification(
        id=str(uuid.uuid4()),
        listing_id=listing_id,
        owner_id_doc_url=owner_url,
        ownership_doc_url=ownership_url,
        match_status=verify_result.get("match_status"),
        match_score=verify_result.get("match_score"),
        match_details=verify_result,
    )
    
    db.add(verification)
    listing.status = ListingStatus.docs_verified
    listing.verification = verification
    
    await db.commit()
    
    return {
        "verification": verify_result,
        "status": listing.status.value,
    }


# ══════════════════════════════════════════════════════════════════════════
# Set Price
# ══════════════════════════════════════════════════════════════════════════
=======
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
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b

@router.post("/{listing_id}/set-price")
async def set_price(
    listing_id: str,
<<<<<<< HEAD
    price: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """تعيين السعر أو استخدام التقدير التلقائي"""
    listing = await db.get(Listing, listing_id)
    if not listing or str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    
    if price <= 0:
        # احسب السعر التقديري
        ai = get_ai_service()
        price_result = await ai.estimate_price(
            category=listing.category.value,
            listing_type=listing.listing_type.value,
            condition_grade=listing.condition_grade.value if listing.condition_grade else "good",
            details=listing.details or {}
        )
        price = price_result.get("estimated_price", 1000000)
    
    # تحقق من سقف الأسعار
    price_caps = settings.PRICE_CAPS.get(listing.category.value, {})
    max_price = price_caps.get(listing.listing_type.value, {}).get(
        listing.condition_grade.value if listing.condition_grade else "good", 
        9999999
    )
    
    if price > max_price:
        raise HTTPException(400, f"السعر يتجاوز الحد الأقصى: {max_price}")
    
    listing.price = price
    listing.status = ListingStatus.price_set
    
    await db.commit()
    
    return {
        "price": price,
        "status": listing.status.value,
    }


# ══════════════════════════════════════════════════════════════════════════
# Publish Listing
# ══════════════════════════════════════════════════════════════════════════

@router.post("/{listing_id}/publish")
async def publish_listing(
    listing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """نشر الإعلان"""
    listing = await db.get(Listing, listing_id)
    if not listing or str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")
    
    # تحقق من جميع الخطوات
    if listing.status not in [ListingStatus.price_set, ListingStatus.pending_review]:
        raise HTTPException(400, f"لا يمكن نشر الإعلان من حالة {listing.status.value}")
    
    listing.status = ListingStatus.published
    listing.published_at = datetime.utcnow()
    
    await db.commit()
    
    return {"status": listing.status.value, "published_at": listing.published_at}


# ══════════════════════════════════════════════════════════════════════════
# List/Search Listings
# ══════════════════════════════════════════════════════════════════════════

@router.get("/")
async def list_listings(
    category: Optional[str] = None,
    listing_type: Optional[str] = None,
    city: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """قائمة بجميع الإعلانات المنشورة"""
    query = select(Listing).where(Listing.status == ListingStatus.published)
    
    if category:
        query = query.where(Listing.category == ListingCategory[category])
    if listing_type:
        query = query.where(Listing.listing_type == ListingType[listing_type])
    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    
    query = query.order_by(desc(Listing.published_at)).offset(skip).limit(limit)
    
    result = await db.execute(query)
    listings = result.scalars().all()
    
    return [
        {
            "id": str(l.id),
            "title": l.title,
            "category": l.category.value,
            "listing_type": l.listing_type.value,
            "price": l.price,
            "city": l.city,
            "condition_grade": l.condition_grade.value if l.condition_grade else None,
            "cover_image": l.images[0].url if l.images else None,
            "seller_id": str(l.seller_id),
        }
        for l in listings
    ]


# ══════════════════════════════════════════════════════════════════════════
# Get Listing Details
# ══════════════════════════════════════════════════════════════════════════

@router.get("/{listing_id}")
async def get_listing(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """تفاصيل الإعلان"""
    listing = await db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")
    
    # زيادة عداد المشاهدات
    listing.view_count += 1
    await db.commit()
    
    return {
        "id": str(listing.id),
        "title": listing.title,
        "description": listing.description,
        "category": listing.category.value,
        "listing_type": listing.listing_type.value,
        "price": listing.price,
        "city": listing.city,
        "district": listing.district,
        "condition_grade": listing.condition_grade.value if listing.condition_grade else None,
        "condition_score": listing.condition_score,
        "details": listing.details,
        "view_count": listing.view_count,
        "images": [{"url": img.url, "type": img.image_type} for img in listing.images],
        "seller_id": str(listing.seller_id),
        "published_at": listing.published_at.isoformat() if listing.published_at else None,
    }
=======
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
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
