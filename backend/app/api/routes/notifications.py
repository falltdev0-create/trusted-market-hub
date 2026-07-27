# ── إضافات لـ notifications.py ────────────────────────────────────────────

from sqlalchemy import and_

@router.post("/send")
async def send_notification(
    user_id: str,
    type: str,
    title: str,
    body: str,
    payload: dict = None,
    db: AsyncSession = Depends(get_db),
):
    """إرسال إشعار (للنظام الداخلي)"""
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
        raise HTTPException(404, "الإشعار غير موجود")
    
    notif.is_read = True
    await db.commit()
    return {"ok": True}