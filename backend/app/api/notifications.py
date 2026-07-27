"""
app/api/routes/notifications.py — الإشعارات
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from app.core.database import get_db
from app.models.models import Notification
from app.api.routes.auth import get_current_user
from app.models.models import User

router = APIRouter()


@router.get("/")
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Notification)
        .where(Notification.user_id == str(current_user.id))
        .order_by(Notification.created_at.desc())
        .limit(50)
    )).scalars().all()

    return [
        {
            "id":         str(n.id),
            "type":       n.type,
            "title":      n.title,
            "body":       n.body,
            "is_read":    n.is_read,
            "payload":    n.payload,
            "created_at": n.created_at.isoformat(),
        }
        for n in rows
    ]


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = (await db.execute(
        select(func.count()).select_from(Notification)
        .where(
            Notification.user_id == str(current_user.id),
            Notification.is_read == False,
        )
    )).scalar()
    return {"count": count, "unread": count}


@router.post("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notif = (await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == str(current_user.id),
        )
    )).scalar_one_or_none()
    if not notif:
        raise HTTPException(404, "الإشعار غير موجود")
    notif.is_read = True
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Notification).where(
            Notification.user_id == str(current_user.id),
            Notification.is_read == False,
        )
    )).scalars().all()

    for n in rows:
        n.is_read = True
    await db.commit()
    return {"ok": True, "marked": len(rows)}
