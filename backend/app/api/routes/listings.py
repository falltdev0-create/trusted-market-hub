"""
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

router = APIRouter()


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

@router.post("/{listing_id}/set-price")
async def set_price(
    listing_id: str,
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