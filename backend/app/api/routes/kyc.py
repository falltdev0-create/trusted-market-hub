# backend/app/api/routes/kyc.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
import json
import uuid
from datetime import date
from typing import Optional
import os
import tempfile

from app.services.storage_service import get_storage_service
from app.models.models import User, KYCStatus
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.services.kyc.passport_service import passport_service
from app.services.kyc.face_service import face_service

router = APIRouter()

# عتبات قرار الوجه (تشابه cosine لنموذج SFace). عايرها على صور هويات حقيقية لديكم.
FACE_REJECT_BELOW = 0.20   # أقل من هذا = وجهان مختلفان بوضوح → رفض آلي
FACE_REVIEW_BELOW = 0.363  # بين العتبتين → للمشرف مع علامة "غير مؤكد"


def _ai_decision(face: dict, passport: Optional[dict]):
    """يرجع (سبب_الرفض أو None, علامات للمشرف). الرفض الآلي لحالات الوضوح فقط."""
    flags: list = []
    verdict = face.get("verdict")
    if verdict == "no_face":
        if not face.get("selfie_face_found"):
            return "لم يتم العثور على وجه واضح في صورة السيلفي. التقط صورة أوضح بإضاءة جيدة", flags
        if not face.get("id_face_found"):
            return "لم يتم العثور على صورة الوجه في وثيقة الهوية. ارفع صورة أوضح للوثيقة", flags
    elif verdict in ("match", "no_match"):
        score = face.get("score")
        if score is not None and score < FACE_REJECT_BELOW:
            return "صورة السيلفي لا تطابق صورة الوجه في وثيقة الهوية", flags
        if score is not None and score < FACE_REVIEW_BELOW:
            flags.append("face_uncertain")
    else:
        flags.append("face_not_checked")
    if passport:
        expiry = passport.get("date_of_expiry")
        if expiry and expiry < date.today().isoformat():
            return "جواز السفر منتهي الصلاحية", flags
    else:
        flags.append("passport_not_read")
    return None, flags


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

        # ---------------------------------------------------------
    # Passport OCR
    # ---------------------------------------------------------

    temp_path = None
    passport_data = None

    try:
        suffix = os.path.splitext(
            id_document.filename or ".jpg"
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(id_content)
            temp_path = temp_file.name

        print("\nRunning Passport OCR...")

        passport_data = await asyncio.to_thread(
            passport_service.extract_passport_data, temp_path
        )

        print("\nPassport data extracted:")
        for key, value in passport_data.items():
            print(f"{key}: {value}")

    except Exception as e:
        # لا نوقف عملية التوثيق كاملة لو فشلت قراءة الجواز (مثلاً بيئة
        # OCR/torch غير جاهزة على السيرفر) — تُحفظ الوثائق ويُكمل المشرف المراجعة يدوياً.
        print(f"⚠️ Passport OCR failed, continuing without it: {e}")

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

    # ---------------------------------------------------------
    # مطابقة الوجه (استرشادية للمشرف — لا ترفع استثناءً ولا تقبل تلقائياً)
    # ---------------------------------------------------------
    face_result = await asyncio.to_thread(
        face_service.compare, id_content, selfie_content
    )
    ai_report = {
        "face": face_result,
        "passport": {
            key: passport_data.get(key)
            for key in ("document_type", "country", "surname", "given_names",
                        "nationality", "date_of_birth", "sex", "date_of_expiry")
        } if passport_data else None,
    }
    reject_reason, flags = _ai_decision(face_result, passport_data)
    ai_report["flags"] = flags
    if reject_reason:
        # رفض آلي: لا نخزّن الوثائق ولا نغيّر حالة المستخدم
        raise HTTPException(422, reject_reason)

            
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

    await db.execute(text("""INSERT INTO kyc_submissions
        (id, user_id, id_front_url, selfie_url, national_id, match_score,
         ai_report_json, status, created_at)
        VALUES (:id, :uid, :doc, :selfie, :nid, :score, :report, 'pending', NOW())"""), {
        "id": str(uuid.uuid4()),
        "uid": str(current_user.id),
        "doc": id_url,
        "selfie": selfie_url,
        "nid": (passport_data or {}).get("passport_number"),
        "score": face_result.get("score"),
        "report": json.dumps(ai_report, ensure_ascii=False, default=str),
    })

    await db.commit()
    await db.refresh(current_user)

    return {
        "message": "تم استلام طلبك واجتاز الفحص الآلي، وهو بانتظار تأكيد المشرف",
        "kyc_status": current_user.kyc_status.value,
        "id_document": id_url,
        "selfie": selfie_url,
    }