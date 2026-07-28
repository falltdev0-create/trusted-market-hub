"""
app/api/routes/admin.py — Hierarchical Admin Panel
Roles: super_admin > admin > moderator > reviewer.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from app.core.database import get_db
from app.models.models import (
    Listing, ListingStatus, ListingVerification, User, Notification,
)
from app.api.routes.auth import get_current_user

log = logging.getLogger("admin")
router = APIRouter()

# ══════════════════════════════════════════════════════════════════════════
# Hierarchy: map roles to allowed permission keys
# ══════════════════════════════════════════════════════════════════════════
ROLE_PERMISSIONS = {
    "super_admin": {"*"},
    "admin": {
        "listings.review", "listings.approve", "listings.reject",
        "users.view", "users.suspend", "kyc.review",
        "reports.handle", "settings.view", "moderators.manage", "logs.view",
    },
    "moderator": {
        "listings.review", "listings.approve", "listings.reject",
        "kyc.review", "reports.handle", "users.view", "logs.view",
    },
    "reviewer": {"listings.review", "kyc.review", "users.view"},
}
ROLE_LEVEL = {"super_admin": 4, "admin": 3, "moderator": 2, "reviewer": 1}


async def _get_admin_role(user: User, db: AsyncSession) -> Optional[str]:
    """Look up the admin role for the given user. Falls back to legacy User.role='admin'."""
    try:
        # Try the modern `admins` table via raw SQL to avoid tight coupling.
        row = (await db.execute(
            select(func.coalesce(None)).where(False)  # noop placeholder
        )).first()
    except Exception:
        pass
    try:
        from sqlalchemy import text
        r = await db.execute(
            text("SELECT role FROM admins WHERE user_id = :uid AND is_active = 1 LIMIT 1"),
            {"uid": str(user.id)},
        )
        row = r.first()
        if row and row[0]:
            return row[0]
    except Exception as e:
        log.debug("admins table lookup failed (using legacy role): %s", e)

    # Legacy fallback: User.role
    legacy = getattr(user, "role", None)
    if legacy:
        val = legacy.value if hasattr(legacy, "value") else str(legacy)
        if val == "admin":
            return "admin"
    return None


async def require_admin_role(min_role: str = "reviewer"):
    """Dependency factory that ensures caller has at least `min_role`."""
    async def _dep(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        role = await _get_admin_role(user, db)
        if not role:
            raise HTTPException(403, "صلاحيات المشرف مطلوبة")
        if ROLE_LEVEL.get(role, 0) < ROLE_LEVEL.get(min_role, 0):
            raise HTTPException(403, f"يتطلب صلاحية {min_role}")
        # attach for handlers
        setattr(user, "admin_role", role)
        return user
    return _dep


async def _log_action(
    db: AsyncSession, admin_user: User, action_type: str,
    target_type: Optional[str] = None, target_id: Optional[str] = None,
    details: Optional[dict] = None,
):
    try:
        from sqlalchemy import text
        # find admin.id
        r = await db.execute(
            text("SELECT id FROM admins WHERE user_id = :uid LIMIT 1"),
            {"uid": str(admin_user.id)},
        )
        row = r.first()
        admin_id = row[0] if row else None
        if not admin_id:
            return
        import json
        await db.execute(
            text("""INSERT INTO admin_actions_log
                  (id, admin_id, action_type, target_type, target_id, details, created_at)
                  VALUES (:id, :admin_id, :at, :tt, :ti, :det, NOW())"""),
            {
                "id": str(uuid.uuid4()), "admin_id": admin_id, "at": action_type,
                "tt": target_type, "ti": target_id,
                "det": json.dumps(details or {}, ensure_ascii=False),
            },
        )
        await db.commit()
    except Exception as e:
        log.debug("action log skipped: %s", e)


# ══════════════════════════════════════════════════════════════════════════
# Pydantic
# ══════════════════════════════════════════════════════════════════════════
class ApproveIn(BaseModel):
    listing_id: str
    admin_id: Optional[str] = None


class RejectIn(BaseModel):
    listing_id: str
    admin_id: Optional[str] = None
    reason: str


class CreateAdminIn(BaseModel):
    user_id: str
    role: str
    permissions: Optional[List[str]] = None


class UpdateAdminIn(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[str]] = None


class KycDecisionIn(BaseModel):
    decision: str  # "approved" | "rejected"
    note: Optional[str] = None


class ReportResolveIn(BaseModel):
    note: str


class SettingIn(BaseModel):
    value: object


# ══════════════════════════════════════════════════════════════════════════
# Dashboard
# ══════════════════════════════════════════════════════════════════════════
@router.get("/dashboard-stats")
async def dashboard_stats(
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    async def _count(status: ListingStatus) -> int:
        r = await db.execute(select(func.count()).select_from(Listing).where(Listing.status == status))
        return r.scalar() or 0

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    try:
        from sqlalchemy import text
        total_admins = (await db.execute(text("SELECT COUNT(*) FROM admins WHERE is_active = 1"))).scalar() or 0
    except Exception:
        total_admins = 0

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "pending_review": await _count(ListingStatus.pending_review),
        "published": await _count(ListingStatus.published),
        "rejected": await _count(ListingStatus.rejected),
        "sold": await _count(ListingStatus.sold),
        "admin_role": getattr(admin, "admin_role", None),
    }


# ══════════════════════════════════════════════════════════════════════════
# Listings review
# ══════════════════════════════════════════════════════════════════════════
@router.get("/pending-listings")
async def pending_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Listing)
        .where(Listing.status == ListingStatus.pending_review)
        .order_by(Listing.updated_at.asc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()
    return [{
        "id": str(l.id), "title": l.title,
        "category": l.category.value if l.category else None,
        "listing_type": l.listing_type.value if l.listing_type else None,
        "price": l.price, "city": l.city,
        "condition_grade": l.condition_grade.value if l.condition_grade else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in rows]


@router.get("/listing/{listing_id}/full-review")
async def full_review(
    listing_id: str,
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    listing = (await db.execute(select(Listing).where(Listing.id == listing_id))).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)
    verif = (await db.execute(select(ListingVerification).where(ListingVerification.listing_id == listing_id))).scalar_one_or_none()
    return {
        "listing": {
            "id": str(listing.id), "title": listing.title,
            "category": listing.category.value if listing.category else None,
            "listing_type": listing.listing_type.value if listing.listing_type else None,
            "status": listing.status.value if listing.status else None,
            "condition_grade": listing.condition_grade.value if listing.condition_grade else None,
            "condition_score": listing.condition_score,
            "condition_report": listing.condition_report,
            "price": listing.price, "details": listing.details,
            "images": [{"url": i.url, "type": i.image_type} for i in (listing.images or [])],
        },
        "verification": {
            "id_doc_url": verif.owner_id_doc_url if verif else None,
            "ownership_doc_url": verif.ownership_doc_url if verif else None,
            "match_score": verif.match_score if verif else None,
            "match_status": verif.match_status.value if verif and verif.match_status else None,
        } if verif else None,
    }


@router.post("/approve-listing")
async def approve_listing(
    body: ApproveIn,
    admin: User = Depends(await require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    listing = (await db.execute(select(Listing).where(Listing.id == body.listing_id))).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)
    listing.status = ListingStatus.published
    listing.published_at = datetime.utcnow()
    db.add(Notification(
        id=str(uuid.uuid4()), user_id=str(listing.seller_id),
        type="listing_approved", title="تم قبول إعلانك",
        body=f"تم نشر إعلانك: {listing.title}", is_read=False,
    ))
    await db.commit()
    await _log_action(db, admin, "listing.approve", "listing", body.listing_id)
    return {"status": "published", "listing_id": body.listing_id}


@router.post("/reject-listing")
async def reject_listing(
    body: RejectIn,
    admin: User = Depends(await require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    listing = (await db.execute(select(Listing).where(Listing.id == body.listing_id))).scalar_one_or_none()
    if not listing:
        raise HTTPException(404)
    listing.status = ListingStatus.rejected
    listing.rejected_reason = body.reason
    db.add(Notification(
        id=str(uuid.uuid4()), user_id=str(listing.seller_id),
        type="listing_rejected", title="تم رفض إعلانك",
        body=body.reason, is_read=False,
    ))
    await db.commit()
    await _log_action(db, admin, "listing.reject", "listing", body.listing_id, {"reason": body.reason})
    return {"status": "rejected", "reason": body.reason}


# ══════════════════════════════════════════════════════════════════════════
# Users
# ══════════════════════════════════════════════════════════════════════════
@router.get("/users")
async def list_users(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).order_by(desc(User.created_at))
    if q:
        like = f"%{q}%"
        stmt = stmt.where((User.full_name.ilike(like)) | (User.email.ilike(like)))
    rows = (await db.execute(stmt.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return [{
        "id": str(u.id), "full_name": u.full_name, "email": u.email, "phone": u.phone,
        "kyc_status": u.kyc_status.value if u.kyc_status else "unverified",
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    } for u in rows]


@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    admin: User = Depends(await require_admin_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404)
    u.is_active = False
    await db.commit()
    await _log_action(db, admin, "user.suspend", "user", user_id)
    return {"ok": True}


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    admin: User = Depends(await require_admin_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    u = await db.get(User, user_id)
    if not u:
        raise HTTPException(404)
    u.is_active = True
    await db.commit()
    await _log_action(db, admin, "user.activate", "user", user_id)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════
# KYC review
# ══════════════════════════════════════════════════════════════════════════
@router.get("/kyc")
async def list_kyc(
    status: str = "pending",
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    try:
        rows = (await db.execute(
            text("""SELECT k.id, k.user_id, k.id_front_url, k.selfie_url, k.status,
                           u.full_name, u.email
                    FROM kyc_submissions k
                    LEFT JOIN users u ON u.id = k.user_id
                    WHERE k.status = :s
                    ORDER BY k.created_at DESC LIMIT 100"""),
            {"s": status},
        )).mappings().all()
        return [{
            "id": r["id"], "user_id": r["user_id"],
            "id_front_url": r["id_front_url"], "selfie_url": r["selfie_url"],
            "status": r["status"],
            "user": {"full_name": r["full_name"], "email": r["email"]},
        } for r in rows]
    except Exception:
        return []


@router.post("/kyc/{kyc_id}/review")
async def review_kyc(
    kyc_id: str, body: KycDecisionIn,
    admin: User = Depends(await require_admin_role("reviewer")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(400, "قرار غير صالح")
    r = await db.execute(text("SELECT user_id FROM kyc_submissions WHERE id = :id"), {"id": kyc_id})
    row = r.first()
    if not row:
        raise HTTPException(404)
    user_id = row[0]
    await db.execute(text("""UPDATE kyc_submissions
        SET status = :s, reviewed_by = :rb, reviewed_at = NOW(), rejection_reason = :rr
        WHERE id = :id"""),
        {"s": body.decision, "rb": str(admin.id), "rr": body.note, "id": kyc_id})
    new_kyc = "verified" if body.decision == "approved" else "rejected"
    await db.execute(text("UPDATE users SET kyc_status = :k WHERE id = :id"), {"k": new_kyc, "id": user_id})
    db.add(Notification(
        id=str(uuid.uuid4()), user_id=user_id,
        type="kyc_" + body.decision,
        title="تم قبول التحقق" if body.decision == "approved" else "تم رفض التحقق",
        body=body.note or "", is_read=False,
    ))
    await db.commit()
    await _log_action(db, admin, "kyc." + body.decision, "kyc", kyc_id)
    return {"ok": True, "kyc_status": new_kyc}


# ══════════════════════════════════════════════════════════════════════════
# Admin hierarchy management (super_admin only)
# ══════════════════════════════════════════════════════════════════════════
@router.get("/admins")
async def list_admins(
    admin: User = Depends(await require_admin_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    rows = (await db.execute(
        text("""SELECT a.id, a.user_id, a.role, a.is_active, a.created_at,
                       u.full_name, u.email
                FROM admins a LEFT JOIN users u ON u.id = a.user_id
                ORDER BY a.created_at DESC""")
    )).mappings().all()
    return [{
        "id": r["id"], "user_id": r["user_id"], "role": r["role"],
        "is_active": bool(r["is_active"]),
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "user": {"full_name": r["full_name"], "email": r["email"]},
    } for r in rows]


@router.post("/admins")
async def create_admin(
    body: CreateAdminIn,
    admin: User = Depends(await require_admin_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    if body.role not in ROLE_LEVEL:
        raise HTTPException(400, "دور غير صالح")
    from sqlalchemy import text
    u = await db.get(User, body.user_id)
    if not u:
        raise HTTPException(404, "المستخدم غير موجود")
    import json
    new_id = str(uuid.uuid4())
    await db.execute(text("""INSERT INTO admins (id, user_id, role, permissions, created_by, is_active, created_at)
        VALUES (:id, :uid, :role, :perms, :cb, 1, NOW())
        ON DUPLICATE KEY UPDATE role = :role, is_active = 1"""),
        {"id": new_id, "uid": body.user_id, "role": body.role,
         "perms": json.dumps(body.permissions or []), "cb": str(admin.id)})
    await db.commit()
    await _log_action(db, admin, "admin.create", "admin", body.user_id, {"role": body.role})
    return {"ok": True, "id": new_id}


@router.patch("/admins/{admin_id}")
async def update_admin(
    admin_id: str, body: UpdateAdminIn,
    admin: User = Depends(await require_admin_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    fields, params = [], {"id": admin_id}
    if body.role is not None:
        if body.role not in ROLE_LEVEL: raise HTTPException(400)
        fields.append("role = :role"); params["role"] = body.role
    if body.is_active is not None:
        fields.append("is_active = :ia"); params["ia"] = 1 if body.is_active else 0
    if body.permissions is not None:
        import json
        fields.append("permissions = :p"); params["p"] = json.dumps(body.permissions)
    if not fields:
        return {"ok": True}
    await db.execute(text(f"UPDATE admins SET {', '.join(fields)} WHERE id = :id"), params)
    await db.commit()
    await _log_action(db, admin, "admin.update", "admin", admin_id, body.dict(exclude_none=True))
    return {"ok": True}


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: str,
    admin: User = Depends(await require_admin_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    await db.execute(text("DELETE FROM admins WHERE id = :id AND role != 'super_admin'"), {"id": admin_id})
    await db.commit()
    await _log_action(db, admin, "admin.delete", "admin", admin_id)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════
# Actions log
# ══════════════════════════════════════════════════════════════════════════
@router.get("/actions-log")
async def actions_log(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin: User = Depends(await require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    rows = (await db.execute(
        text("""SELECT l.id, l.admin_id, l.action_type, l.target_type, l.target_id,
                       l.details, l.created_at, u.full_name
                FROM admin_actions_log l
                LEFT JOIN admins a ON a.id = l.admin_id
                LEFT JOIN users u  ON u.id = a.user_id
                ORDER BY l.created_at DESC
                LIMIT :lim OFFSET :off"""),
        {"lim": page_size, "off": (page - 1) * page_size},
    )).mappings().all()
    return [{
        "id": r["id"], "admin_id": r["admin_id"], "action_type": r["action_type"],
        "target_type": r["target_type"], "target_id": r["target_id"],
        "details": r["details"], "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "admin": {"full_name": r["full_name"]},
    } for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# Reports
# ══════════════════════════════════════════════════════════════════════════
@router.get("/reports")
async def list_reports(
    status: str = "open",
    admin: User = Depends(await require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    try:
        rows = (await db.execute(
            text("SELECT * FROM reports WHERE status = :s ORDER BY created_at DESC LIMIT 200"),
            {"s": status},
        )).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


@router.post("/reports/{report_id}/resolve")
async def resolve_report(
    report_id: str, body: ReportResolveIn,
    admin: User = Depends(await require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    await db.execute(text("""UPDATE reports SET status='resolved', resolved_by=:rb,
                     resolved_at=NOW(), resolution_note=:n WHERE id=:id"""),
        {"rb": str(admin.id), "n": body.note, "id": report_id})
    await db.commit()
    await _log_action(db, admin, "report.resolve", "report", report_id)
    return {"ok": True}


# ══════════════════════════════════════════════════════════════════════════
# Settings
# ══════════════════════════════════════════════════════════════════════════
@router.get("/settings")
async def get_settings_ep(
    admin: User = Depends(await require_admin_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    try:
        rows = (await db.execute(text("SELECT setting_key, setting_value FROM system_settings"))).mappings().all()
        return {r["setting_key"]: r["setting_value"] for r in rows}
    except Exception:
        return {}


@router.put("/settings/{key}")
async def update_setting(
    key: str, body: SettingIn,
    admin: User = Depends(await require_admin_role("super_admin")),
    db: AsyncSession = Depends(get_db),
):
    import json
    from sqlalchemy import text
    await db.execute(text("""INSERT INTO system_settings (setting_key, setting_value, updated_by, updated_at)
        VALUES (:k, :v, :ub, NOW())
        ON DUPLICATE KEY UPDATE setting_value = :v, updated_by = :ub, updated_at = NOW()"""),
        {"k": key, "v": json.dumps(body.value, ensure_ascii=False), "ub": str(admin.id)})
    await db.commit()
    await _log_action(db, admin, "setting.update", "setting", key)
    return {"ok": True}
