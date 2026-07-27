"""
app/api/routes/verification.py — التحقق من المستندات والصور
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import ListingVerification, Listing
from app.api.routes.auth import get_current_user
from app.models.models import User
from app.services.ai_service import get_ai_service

router = APIRouter()


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