from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.storage_service import get_storage_service
from app.models.models import User, KYCStatus
from app.api.routes.auth import get_current_user

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User

router = APIRouter(prefix="/kyc", tags=["KYC"])


@router.get("/health")
async def kyc_health():
    return {"message": "KYC API is working"}


@router.post("/submit")
async def submit_kyc(
    id_document: UploadFile = File(...),
    selfie: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    storage_service = get_storage_service()
    #read the uploaded files
    id_content = await id_document.read()
    selfie_content = await selfie.read()

    # upload the documents to storage service
    id_url = await storage_service.upload_kyc_document(
        content=id_content,
        filename=id_document.filename,
        user_id=str(current_user.id),
        doc_type="id_document",
    )

    selfie_url = await storage_service.upload_kyc_document(
        content=selfie_content,
        filename=selfie.filename,
        user_id=str(current_user.id),
        doc_type="selfie",
    )

    # update the user's KYC status and document URLs in the database
    current_user.kyc_doc_url = id_url
    current_user.selfie_url = selfie_url
    current_user.kyc_status = KYCStatus.pending

    await db.commit()
    await db.refresh(current_user)

    return {
        "message": "KYC submitted successfully",
        "kyc_status": current_user.kyc_status.value,
        "id_document": id_url,
        "selfie": selfie_url,
    }