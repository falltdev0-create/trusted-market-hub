"""
app/api/routes/verification.py — التحقق من المستندات والصور
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime

from app.core.database import get_db
from app.models.models import ListingVerification, Listing, ListingStatus, DocMatchStatus
from app.api.routes.auth import get_current_user
from app.models.models import User
from app.services.ai_service import get_ai_service
from app.services.storage_service import get_storage_service

router = APIRouter()


@router.post("/{listing_id}/upload-documents")
async def upload_documents(
    listing_id: str,
    id_document: UploadFile = File(...),
    ownership_document: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """رفع وثائق الإعلان ومطابقة الهوية مع الملكية عبر نموذج AI أو fallback آمن."""
    listing = await db.get(Listing, listing_id)
    if not listing or str(listing.seller_id) != str(current_user.id):
        raise HTTPException(403, "غير مصرح")

    id_bytes = await id_document.read()
    own_bytes = await ownership_document.read()

    storage = get_storage_service()
    # Rebuild file streams for the storage helper after reading bytes for AI.
    from io import BytesIO
    id_document.file = BytesIO(id_bytes)
    ownership_document.file = BytesIO(own_bytes)
    id_url = await storage.upload_file(id_document, f"listings/{listing_id}/docs")
    own_url = await storage.upload_file(ownership_document, f"listings/{listing_id}/docs")

    ai = get_ai_service()
    result = await ai.match_documents(id_bytes, own_bytes, listing.category.value)
    score = float(result.get("match_score", 0.0))
    passed = bool(result.get("passed", score >= 0.70))

    verification = (await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == listing_id)
    )).scalar_one_or_none()
    if not verification:
        verification = ListingVerification(id=str(uuid.uuid4()), listing_id=listing_id)
        db.add(verification)

    verification.owner_id_doc_url = id_url
    verification.ownership_doc_url = own_url
    verification.match_score = score
    verification.match_status = DocMatchStatus.approved if passed else DocMatchStatus.rejected
    verification.match_details = result
    verification.verified_at = datetime.utcnow() if passed else None
    verification.rejection_reason = None if passed else "لم تتطابق بيانات الهوية مع وثيقة الملكية"
    listing.status = ListingStatus.docs_verified if passed else ListingStatus.docs_uploaded

    await db.commit()
    return {
        "status": listing.status.value,
        "verification": {
            "match_status": verification.match_status.value,
            "match_score": verification.match_score,
            "match_details": verification.match_details,
            "rejection_reason": verification.rejection_reason,
        },
    }


@router.get("/{listing_id}/status")
async def get_verification_status(
    listing_id: str,
    db: AsyncSession = Depends(get_db),
):
    """حالة التحقق من الإعلان"""
    verification = await db.get(ListingVerification, listing_id)
    if not verification:
        raise HTTPException(404, "لم يتم العثور على تحقق")
    
    return {
        "id": str(verification.id),
        "listing_id": str(verification.listing_id),
        "match_status": verification.match_status.value,
        "match_score": verification.match_score,
        "match_details": verification.match_details,
        "rejection_reason": verification.rejection_reason,
        "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
    }


@router.post("/{verification_id}/approve")
async def approve_verification(
    verification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """الموافقة على التحقق (للمسؤولين فقط)"""
    if current_user.role.value != "admin":
        raise HTTPException(403, "غير مصرح")
    
    verification = await db.get(ListingVerification, verification_id)
    if not verification:
        raise HTTPException(404, "لم يتم العثور على تحقق")
    
    from datetime import datetime
    verification.match_status = "approved"
    verification.verified_at = datetime.utcnow()
    
    await db.commit()
    return {"status": "approved"}


@router.post("/{verification_id}/reject")
async def reject_verification(
    verification_id: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """رفض التحقق (للمسؤولين فقط)"""
    if current_user.role.value != "admin":
        raise HTTPException(403, "غير مصرح")
    
    verification = await db.get(ListingVerification, verification_id)
    if not verification:
        raise HTTPException(404, "لم يتم العثور على تحقق")
    
    verification.match_status = "rejected"
    verification.rejection_reason = reason
    
    await db.commit()
    return {"status": "rejected", "reason": reason}