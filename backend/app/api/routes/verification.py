"""
app/api/routes/verification.py — التحقق من وثائق الملكية
يستقبل الوثائق → يشغّل AI المطابقة → يحدّث حالة الإعلان
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.models import (
    Listing, ListingVerification, ListingStatus, DocMatchStatus
)
from app.services.storage_service import storage_service
from app.services.ai_service import ai_service

router = APIRouter()

MATCH_THRESHOLD = 70.0


@router.post("/{listing_id}/upload-documents")
async def upload_documents(
    listing_id: str,
    owner_id_doc:  UploadFile = File(..., description="صورة بطاقة الهوية الوطنية"),
    ownership_doc: UploadFile = File(..., description="وثيقة الملكية (عقد / استمارة سيارة)"),
    db: AsyncSession = Depends(get_db),
):
    """
    يرفع وثيقتي التحقق ويشغّل AI المطابقة.
    النجاح: match_score ≥ 70 → docs_verified
    الفشل:  match_score < 70 → docs_uploaded (يمكن إعادة المحاولة)
    """
    result  = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")

    if listing.status not in [ListingStatus.condition_assessed, ListingStatus.docs_uploaded]:
        raise HTTPException(400, "يجب إتمام تقييم الحالة بالصور أولاً")

    id_bytes  = await owner_id_doc.read()
    own_bytes = await ownership_doc.read()

    # Upload to storage
    id_url  = await storage_service.upload_document(id_bytes,  owner_id_doc.filename,  listing_id, "id_doc")
    own_url = await storage_service.upload_document(own_bytes, ownership_doc.filename, listing_id, "ownership_doc")

    # AI document matching
    match_result = await ai_service.match_documents(id_bytes, own_bytes, listing.category.value)

    passed = match_result.get("passed", False) or match_result["match_score"] >= MATCH_THRESHOLD
    status = DocMatchStatus.approved if passed else DocMatchStatus.rejected

    # Upsert verification record
    verif_result = await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(listing_id))
    )
    verif = verif_result.scalar_one_or_none()

    if verif:
        verif.owner_id_doc_url  = id_url
        verif.ownership_doc_url = own_url
        verif.match_score       = match_result["match_score"]
        verif.match_status      = status
        verif.match_details     = match_result
        verif.verified_at       = datetime.utcnow() if passed else None
    else:
        verif = ListingVerification(
            id=uuid.uuid4(),
            listing_id=uuid.UUID(listing_id),
            owner_id_doc_url=id_url,
            ownership_doc_url=own_url,
            match_score=match_result["match_score"],
            match_status=status,
            match_details=match_result,
            verified_at=datetime.utcnow() if passed else None,
        )
        db.add(verif)

    listing.status = ListingStatus.docs_verified if passed else ListingStatus.docs_uploaded
    await db.commit()

    if not passed:
        raise HTTPException(
            422,
            {
                "message":     "فشل التحقق — لم يثبت التطابق بين الهوية ووثيقة الملكية",
                "match_score": match_result["match_score"],
                "issues":      match_result.get("issues", []),
            }
        )

    return {
        "status":      "verified",
        "match_score": match_result["match_score"],
        "message":     "تم التحقق من الوثائق بنجاح ✅",
    }


@router.get("/{listing_id}/verification-status")
async def get_verification_status(listing_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(listing_id))
    )
    verif = result.scalar_one_or_none()
    if not verif:
        return {"status": "not_submitted"}

    return {
        "status":      verif.match_status.value,
        "match_score": verif.match_score,
        "details":     verif.match_details,
        "verified_at": verif.verified_at.isoformat() if verif.verified_at else None,
    }
