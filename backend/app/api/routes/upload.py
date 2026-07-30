"""
app/api/routes/upload.py — رفع الصور وتشغيل AI
يستقبل الصور → يخزنها → يشغّل نموذج التقييم في الخلفية
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.models.models import Listing, ListingImage, ListingStatus, ConditionGrade
from app.services.storage_service import get_storage_service
from app.services.ai_service import get_ai_service
from app.api.routes.auth import get_current_user
from app.models.models import User

router = APIRouter()

# Singletons
storage_service = get_storage_service()
ai_service = get_ai_service()

ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp", "image/heic"}
MAX_IMAGE_SIZE = 20 * 1024 * 1024   # 20 MB


@router.post("/listing/{listing_id}/images")
async def upload_listing_images(
    listing_id: str,
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(..., description="صور السلعة (5-20 صورة)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    يرفع صور السلعة ويشغّل نموذج تقييم الحالة في الخلفية.
    يشترط 5 صور على الأقل لتغطية السلعة من جميع الجوانب.
    """
    if not (5 <= len(images) <= 20):
        raise HTTPException(422, "يجب رفع بين 5 و20 صورة")

    result  = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")
    if str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")

    # Validate & read all images first
    images_data: List[tuple] = []
    for img in images:
        if img.content_type not in ALLOWED_TYPES:
            raise HTTPException(422, f"نوع الملف {img.content_type} غير مدعوم")
        content = await img.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(422, f"الصورة {img.filename} تتجاوز 20 ميجابايت")
        images_data.append((content, img.filename))

    # Upload to storage
    image_urls = []
    for i, (content, filename) in enumerate(images_data):
        url = await storage_service.upload_image(content, filename, listing_id, i)
        image_urls.append(url)
        db.add(ListingImage(
            id=str(uuid.uuid4()),
            listing_id=listing_id,
            url=url,
            image_type="exterior" if i < 3 else "interior",
            order=i,
        ))

    listing.status = ListingStatus.images_uploaded
    await db.commit()

    # AI condition assessment in background
    async def _run_assessment():
        try:
            image_bytes = [d[0] for d in images_data]
            ai_result   = await ai_service.assess_condition(image_bytes, listing.category.value)

            grade = ConditionGrade(ai_result["grade"])

            listing.condition_grade  = grade
            listing.condition_score  = ai_result["score"]
            listing.condition_report = ai_result
            listing.price_max_limit  = None
            listing.status           = ListingStatus.condition_assessed
            await db.commit()
            print(f"✅ AI assessed {listing_id}: {grade.value} ({ai_result['score']})")
        except Exception as e:
            print(f"❌ AI assessment failed for {listing_id}: {e}")

    background_tasks.add_task(_run_assessment)

    return {
        "uploaded":           len(image_urls),
        "urls":               image_urls,
        "status":             "images_uploaded",
        "assessment_status":  "processing",
        "message":            "تم رفع الصور وجاري التحليل بالذكاء الاصطناعي...",
    }


@router.get("/listing/{listing_id}/condition-result")
async def get_condition_result(listing_id: str, db: AsyncSession = Depends(get_db)):
    """استعلام عن نتيجة تقييم الحالة"""
    result  = await db.execute(select(Listing).where(Listing.id == listing_id))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404)

    if listing.status == ListingStatus.images_uploaded:
        return {"status": "processing", "message": "جاري التحليل..."}
    if not listing.condition_grade:
        return {"status": "pending"}

    return {
        "status":          "done",
        "condition_grade": listing.condition_grade.value,
        "condition_score": listing.condition_score,
        "price_max_limit": None,
        "price_tier":      listing.price_tier,
        "currency":        listing.currency,
        "report":          listing.condition_report,
    }
