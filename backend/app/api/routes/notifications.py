# src/backend/app/api/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.models.models import User, Notification

router = APIRouter()


@router.post("/send")
async def send_notification(
    user_id: str,
    type: str,
    title: str,
    body: str,
    payload: dict | None = None,
    db: AsyncSession = Depends(get_db),
):
    """إرسال إشعار للنظام الداخلي"""

    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        payload=payload or {},
    )

    db.add(notification)
    await db.commit()
    await db.refresh(notification)

    return {"id": notification.id}


@router.patch("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """تعليم إشعار كمقروء"""

    notif = await db.get(Notification, notification_id)

    if not notif or str(notif.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=404,
            detail="الإشعار غير موجود",
        )

    notif.is_read = True

    await db.commit()

    return {"ok": True}