"""
Verification Routes — مسارات التحقق من الوثائق
يستقبل الوثائق ويستدعي نموذج AI للمطابقة
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.listing import Listing, ListingVerification, ListingStatus, VerificationStatus
from app.services.storage_service import StorageService
from app.services.ai_service import AIService

router = APIRouter()
storage = StorageService()
ai_service = AIService()


@router.post("/{listing_id}/upload-documents")
async def upload_verification_documents(
    listing_id: str,
    owner_id_doc: UploadFile = File(..., description="صورة بطاقة الهوية الوطنية للمالك"),
    ownership_doc: UploadFile = File(..., description="وثيقة الملكية (عقد+سند / استمارة سيارة)"),
    db: AsyncSession = Depends(get_db),
):
    """
    رفع وثيقتي التحقق وتشغيل نموذج المطابقة.
    يتحقق من أن:
    1. الاسم في وثيقة الهوية يطابق (أو قريب درجة أولى) الاسم في وثيقة الملكية.
    2. رقم الهوية / رقم التسجيل متطابق.
    """
    # Load listing
    result = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    if listing.status not in [ListingStatus.condition_assessed, ListingStatus.docs_uploaded]:
        raise HTTPException(
            status_code=400,
            detail="يجب إتمام تقييم الحالة أولاً"
        )

    # Upload documents to storage
    id_doc_bytes  = await owner_id_doc.read()
    own_doc_bytes = await ownership_doc.read()

    id_url  = await storage.upload_document(id_doc_bytes,  owner_id_doc.filename,  listing_id, "id_doc")
    own_url = await storage.upload_document(own_doc_bytes, ownership_doc.filename, listing_id, "ownership_doc")

    # Run AI document matching
    match_result = await ai_service.match_documents(
        id_doc_bytes=id_doc_bytes,
        ownership_doc_bytes=own_doc_bytes,
        category=listing.category.value,
    )

    # Determine status
    status = (
        VerificationStatus.approved
        if match_result["match_score"] >= 70
        else VerificationStatus.rejected
    )

    # Save or update verification record
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
    else:
        verif = ListingVerification(
            id=uuid.uuid4(),
            listing_id=uuid.UUID(listing_id),
            owner_id_doc_url=id_url,
            ownership_doc_url=own_url,
            match_score=match_result["match_score"],
            match_status=status,
            match_details=match_result,
        )
        db.add(verif)

    # Update listing status
    listing.status = (
        ListingStatus.docs_verified
        if status == VerificationStatus.approved
        else ListingStatus.docs_uploaded
    )

    await db.commit()

    if status == VerificationStatus.rejected:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "فشل التحقق من الوثائق — لم يثبت التطابق بين الهوية ووثيقة الملكية",
                "match_score": match_result["match_score"],
                "details": match_result.get("issues", []),
            }
        )

    return {
        "status": "verified",
        "match_score": match_result["match_score"],
        "message": "تم التحقق من الوثائق بنجاح ✅",
    }


@router.get("/{listing_id}/verification-status")
async def get_verification_status(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == uuid.UUID(listing_id))
    )
    verif = result.scalar_one_or_none()
    if not verif:
        return {"status": "not_submitted"}

    return {
        "status": verif.match_status.value,
        "match_score": verif.match_score,
        "details": verif.match_details,
    }
