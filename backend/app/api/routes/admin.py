"""
app/api/routes/admin.py — لوحة الإدارة الكاملة
إحصائيات | مراجعة الإعلانات (قبول/رفض/حذف) | إدارة المستخدمين
طلبات التحقق (KYC) | سجل التدقيق | إعدادات الموقع
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional, Any
import uuid

from app.core.database import get_db
from app.core.security import require_admin_role
from app.models.models import (
    Listing, ListingImage, ListingStatus, ListingVerification,
    User, UserRole, KYCStatus, AdminAuditLog, SiteSetting, Notification,
)

router = APIRouter()

Admin      = Depends(require_admin_role("reviewer"))
Moderator  = Depends(require_admin_role("moderator"))
SuperAdmin = Depends(require_admin_role("super_admin"))


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _log(db: AsyncSession, admin: User, action: str,
               target_type: str = None, target_id: str = None, details: dict = None):
    db.add(AdminAuditLog(
        id=uuid.uuid4(),
        admin_id=admin.id,
        admin_name=admin.full_name,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=details or {},
    ))


async def _notify(db: AsyncSession, user_id, type_: str, title: str, body: str = "", payload: dict = None):
    db.add(Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=type_,
        title=title,
        body=body,
        payload=payload or {},
    ))


def _uid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError:
        raise HTTPException(400, "معرّف غير صالح")


def _ser_listing(l: Listing) -> dict:
    return {
        "id":              str(l.id),
        "title":           l.title,
        "description":     l.description,
        "category":        l.category.value,
        "listing_type":    l.listing_type.value,
        "status":          l.status.value,
        "seller_id":       str(l.seller_id),
        "seller_name":     l.seller.full_name if l.seller else None,
        "condition_grade": l.condition_grade.value if l.condition_grade else None,
        "condition_score": l.condition_score,
        "price":           l.price,
        "currency":        l.currency,
        "city":            l.city,
        "view_count":      l.view_count,
        "cover_image":     l.images[0].url if l.images else None,
        "created_at":      l.created_at.isoformat() if l.created_at else None,
        "published_at":    l.published_at.isoformat() if l.published_at else None,
    }


def _ser_user(u: User) -> dict:
    return {
        "id":          str(u.id),
        "full_name":   u.full_name,
        "email":       u.email,
        "phone":       u.phone,
        "role":        u.role.value if u.role else "both",
        "kyc_status":  u.kyc_status.value if u.kyc_status else "pending",
        "is_active":   bool(u.is_active),
        "is_verified": bool(u.is_verified),
        "avatar_url":  u.avatar_url,
        "kyc_doc_url": u.kyc_doc_url,
        "selfie_url":  u.selfie_url,
        "created_at":  u.created_at.isoformat() if u.created_at else None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Stats
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/dashboard-stats")
async def dashboard_stats(admin: User = Admin, db: AsyncSession = Depends(get_db)):
    async def _count(model, *where):
        return (await db.execute(select(func.count()).select_from(model).where(*where))).scalar() or 0

    week_ago = datetime.utcnow() - timedelta(days=7)

    return {
        "total_users":     await _count(User),
        "active_users":    await _count(User, User.is_active == True),  # noqa: E712
        "new_users_week":  await _count(User, User.created_at >= week_ago),
        "total_listings":  await _count(Listing),
        "pending_review":  await _count(Listing, Listing.status == ListingStatus.pending_review),
        "published":       await _count(Listing, Listing.status == ListingStatus.published),
        "rejected":        await _count(Listing, Listing.status == ListingStatus.rejected),
        "sold":            await _count(Listing, Listing.status == ListingStatus.sold),
        "drafts":          await _count(Listing, Listing.status == ListingStatus.draft),
        "kyc_pending":     await _count(User, User.kyc_status == KYCStatus.pending,
                                        User.kyc_doc_url.isnot(None)),
        "admin_role":      getattr(admin, "admin_role", "admin"),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Listings
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/listings")
async def list_listings(
    status:    Optional[str] = None,
    q:         Optional[str] = None,
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Admin,
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if status and status != "all":
        try:
            filters.append(Listing.status == ListingStatus(status))
        except ValueError:
            raise HTTPException(400, "حالة غير معروفة")
    if q:
        filters.append(or_(Listing.title.ilike(f"%{q}%"), Listing.city.ilike(f"%{q}%")))

    total = (await db.execute(
        select(func.count()).select_from(Listing).where(*filters)
    )).scalar() or 0

    rows = (await db.execute(
        select(Listing).where(*filters)
        .order_by(Listing.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [_ser_listing(l) for l in rows],
    }


@router.get("/pending-listings")
async def pending_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Admin,
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Listing).where(Listing.status == ListingStatus.pending_review)
        .order_by(Listing.updated_at.asc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return [_ser_listing(l) for l in rows]


@router.get("/listing/{listing_id}/full-review")
async def full_review(listing_id: str, admin: User = Admin, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(
        select(Listing).where(Listing.id == _uid(listing_id))
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")

    verif = (await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == _uid(listing_id))
    )).scalar_one_or_none()

    data = _ser_listing(listing)
    data.update({
        "condition_report": listing.condition_report,
        "details":          listing.details,
        "images":           [{"url": i.url, "type": i.image_type} for i in (listing.images or [])],
    })

    return {
        "listing": data,
        "verification": {
            "id_doc_url":        verif.owner_id_doc_url,
            "ownership_doc_url": verif.ownership_doc_url,
            "match_score":       verif.match_score,
            "match_status":      verif.match_status.value if verif.match_status else None,
            "match_details":     verif.match_details,
        } if verif else None,
    }


class ApproveIn(BaseModel):
    listing_id: str


class RejectIn(BaseModel):
    listing_id: str
    reason: str


@router.post("/approve-listing")
async def approve_listing(body: ApproveIn, admin: User = Moderator, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(
        select(Listing).where(Listing.id == _uid(body.listing_id))
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")

    listing.status = ListingStatus.published
    listing.published_at = datetime.utcnow()

    await _notify(db, listing.seller_id, "listing_approved",
                  "تم نشر إعلانك ✅", f"إعلان «{listing.title}» أصبح منشوراً في السوق.",
                  {"listing_id": str(listing.id)})
    await _log(db, admin, "approve_listing", "listing", listing.id, {"title": listing.title})
    await db.commit()
    return {"status": "published", "listing_id": str(listing.id)}


@router.post("/reject-listing")
async def reject_listing(body: RejectIn, admin: User = Moderator, db: AsyncSession = Depends(get_db)):
    listing = (await db.execute(
        select(Listing).where(Listing.id == _uid(body.listing_id))
    )).scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")

    listing.status = ListingStatus.rejected

    verif = (await db.execute(
        select(ListingVerification).where(ListingVerification.listing_id == listing.id)
    )).scalar_one_or_none()
    if verif:
        verif.rejection_reason = body.reason
        verif.reviewed_by      = admin.id
        verif.reviewed_at      = datetime.utcnow()

    await _notify(db, listing.seller_id, "listing_rejected",
                  "تم رفض إعلانك", body.reason, {"listing_id": str(listing.id)})
    await _log(db, admin, "reject_listing", "listing", listing.id, {"reason": body.reason})
    await db.commit()
    return {"status": "rejected", "reason": body.reason}


@router.delete("/listing/{listing_id}")
async def delete_listing(listing_id: str, admin: User = Depends(require_admin_role("admin")),
                         db: AsyncSession = Depends(get_db)):
    lid = _uid(listing_id)
    listing = (await db.execute(select(Listing).where(Listing.id == lid))).scalar_one_or_none()
    if not listing:
        raise HTTPException(404, "الإعلان غير موجود")

    title, seller_id = listing.title, listing.seller_id
    await db.execute(delete(ListingImage).where(ListingImage.listing_id == lid))
    await db.execute(delete(ListingVerification).where(ListingVerification.listing_id == lid))
    await db.execute(delete(Listing).where(Listing.id == lid))

    await _notify(db, seller_id, "listing_deleted", "تم حذف إعلانك", f"«{title}» حُذف من المنصة.")
    await _log(db, admin, "delete_listing", "listing", lid, {"title": title})
    await db.commit()
    return {"status": "deleted"}


# ══════════════════════════════════════════════════════════════════════════════
# Users
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/users")
async def list_users(
    q:    Optional[str] = None,
    role: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Admin,
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if q:
        filters.append(or_(
            User.full_name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.phone.ilike(f"%{q}%"),
        ))
    if role and role != "all":
        try:
            filters.append(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(400, "صلاحية غير معروفة")

    total = (await db.execute(select(func.count()).select_from(User).where(*filters))).scalar() or 0
    rows = (await db.execute(
        select(User).where(*filters).order_by(User.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "items": [_ser_user(u) for u in rows],
    }


class UpdateUserIn(BaseModel):
    role:        Optional[str] = None
    is_active:   Optional[bool] = None
    is_verified: Optional[bool] = None
    full_name:   Optional[str] = None


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: UpdateUserIn,
                      admin: User = Depends(require_admin_role("admin")),
                      db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == _uid(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    if body.role is not None:
        try:
            new_role = UserRole(body.role)
        except ValueError:
            raise HTTPException(400, "صلاحية غير معروفة")
        if new_role in (UserRole.admin, UserRole.super_admin) and \
                getattr(admin, "admin_role", "") != "super_admin":
            raise HTTPException(403, "منح صلاحية الإدارة يتطلب مديراً أعلى")
        user.role = new_role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.is_verified is not None:
        user.is_verified = body.is_verified
    if body.full_name:
        user.full_name = body.full_name

    await _log(db, admin, "update_user", "user", user.id, body.model_dump(exclude_none=True))
    await db.commit()
    return _ser_user(user)


class BanIn(BaseModel):
    banned: bool = True
    reason: Optional[str] = None


@router.post("/users/{user_id}/ban")
async def ban_user(user_id: str, body: BanIn,
                   admin: User = Depends(require_admin_role("admin")),
                   db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == _uid(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")
    if user.id == admin.id:
        raise HTTPException(400, "لا يمكنك حظر نفسك")

    user.is_active = not body.banned
    await _notify(db, user.id, "account",
                  "تم حظر حسابك" if body.banned else "تم رفع الحظر عن حسابك",
                  body.reason or "")
    await _log(db, admin, "ban_user" if body.banned else "unban_user", "user", user.id,
               {"reason": body.reason})
    await db.commit()
    return {"id": str(user.id), "is_active": user.is_active}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = SuperAdmin, db: AsyncSession = Depends(get_db)):
    uid = _uid(user_id)
    if uid == admin.id:
        raise HTTPException(400, "لا يمكنك حذف حسابك")
    user = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    email = user.email
    await db.execute(delete(Notification).where(Notification.user_id == uid))
    await db.execute(delete(User).where(User.id == uid))
    await _log(db, admin, "delete_user", "user", uid, {"email": email})
    await db.commit()
    return {"status": "deleted"}


@router.get("/admins")
async def list_admins(admin: User = Admin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(User).where(User.role.in_([UserRole.admin, UserRole.super_admin]))
        .order_by(User.created_at.asc())
    )).scalars().all()
    return [_ser_user(u) for u in rows]


# ══════════════════════════════════════════════════════════════════════════════
# KYC requests
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/kyc-requests")
async def kyc_requests(status: str = "pending", admin: User = Admin,
                       db: AsyncSession = Depends(get_db)):
    filters = [User.kyc_doc_url.isnot(None)]
    if status and status != "all":
        try:
            filters.append(User.kyc_status == KYCStatus(status))
        except ValueError:
            raise HTTPException(400, "حالة غير معروفة")

    rows = (await db.execute(
        select(User).where(*filters).order_by(User.updated_at.desc()).limit(100)
    )).scalars().all()
    return [_ser_user(u) for u in rows]


@router.post("/kyc/{user_id}/approve")
async def approve_kyc(user_id: str, admin: User = Moderator, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == _uid(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    user.kyc_status  = KYCStatus.approved
    user.is_verified = True
    await _notify(db, user.id, "kyc", "تم توثيق حسابك ✅", "يمكنك الآن نشر الإعلانات.")
    await _log(db, admin, "approve_kyc", "user", user.id)
    await db.commit()
    return _ser_user(user)


class KycRejectIn(BaseModel):
    reason: str


@router.post("/kyc/{user_id}/reject")
async def reject_kyc(user_id: str, body: KycRejectIn, admin: User = Moderator,
                     db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.id == _uid(user_id)))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "المستخدم غير موجود")

    user.kyc_status  = KYCStatus.rejected
    user.is_verified = False
    await _notify(db, user.id, "kyc", "تم رفض طلب التوثيق", body.reason)
    await _log(db, admin, "reject_kyc", "user", user.id, {"reason": body.reason})
    await db.commit()
    return _ser_user(user)


# ══════════════════════════════════════════════════════════════════════════════
# Audit log
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/audit-logs")
async def audit_logs(page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100),
                     admin: User = Admin, db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count()).select_from(AdminAuditLog))).scalar() or 0
    rows = (await db.execute(
        select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return {
        "total": total, "page": page,
        "pages": (total + page_size - 1) // page_size,
        "items": [{
            "id":          str(r.id),
            "admin_name":  r.admin_name,
            "action":      r.action,
            "target_type": r.target_type,
            "target_id":   r.target_id,
            "details":     r.details,
            "created_at":  r.created_at.isoformat() if r.created_at else None,
        } for r in rows],
    }


# ══════════════════════════════════════════════════════════════════════════════
# Site settings
# ══════════════════════════════════════════════════════════════════════════════

DEFAULT_SETTINGS: dict[str, Any] = {
    "site_name":          "معاملاتي",
    "maintenance_mode":   False,
    "allow_registration": True,
    "require_kyc":        True,
    "min_images":         3,
    "support_email":      "support@moamalati.sd",
    "support_phone":      "",
}


@router.get("/settings")
async def get_settings(admin: User = Admin, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(SiteSetting))).scalars().all()
    data = dict(DEFAULT_SETTINGS)
    for r in rows:
        data[r.key] = r.value
    return data


class SettingsIn(BaseModel):
    settings: dict


@router.put("/settings")
async def update_settings(body: SettingsIn, admin: User = Depends(require_admin_role("admin")),
                          db: AsyncSession = Depends(get_db)):
    for key, value in body.settings.items():
        row = (await db.execute(select(SiteSetting).where(SiteSetting.key == key))).scalar_one_or_none()
        if row:
            row.value = value
            row.updated_at = datetime.utcnow()
        else:
            db.add(SiteSetting(key=key, value=value))
    await _log(db, admin, "update_settings", "settings", None, body.settings)
    await db.commit()
    return await get_settings(admin, db)
