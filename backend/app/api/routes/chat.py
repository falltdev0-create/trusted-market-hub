"""
app/api/routes/chat.py — المحادثة الفورية
WebSocket داخلي — يمنع تبادل بيانات التواصل الخارجية
"""

import re
import json
import uuid
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel

from app.core.database import get_db
from app.models.models import Conversation, Message, Listing, ListingStatus

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Contact-info filter — يمنع تبادل بيانات التواصل خارج المنصة
# ══════════════════════════════════════════════════════════════════════════════

_CONTACT_RE = re.compile(
    r'|'.join([
        r'\b\+?[\d\s\-\(\)]{9,15}\b',                              # أرقام هاتف
        r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',      # إيميل
        r'\b(whatsapp|واتساب|تيليجرام|telegram|snapchat|سناب|انستا|instagram)\b',
        r'@[a-zA-Z0-9_]{3,30}',                                     # handles
    ]),
    re.IGNORECASE | re.UNICODE,
)


def _sanitize(text: str):
    """Returns (cleaned_text, was_filtered)."""
    if _CONTACT_RE.search(text):
        return _CONTACT_RE.sub("***", text), True
    return text, False


# ══════════════════════════════════════════════════════════════════════════════
# WebSocket Connection Manager
# ══════════════════════════════════════════════════════════════════════════════

class ConnectionManager:
    def __init__(self):
        self._rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, ws: WebSocket):
        await ws.accept()
        self._rooms.setdefault(room, []).append(ws)

    def disconnect(self, room: str, ws: WebSocket):
        if room in self._rooms:
            try:
                self._rooms[room].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, room: str, data: dict):
        for ws in self._rooms.get(room, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


# ── Schemas ───────────────────────────────────────────────────────────────────

class StartConversationIn(BaseModel):
    listing_id: str
    buyer_id:   str


class SignDisclaimerIn(BaseModel):
    conversation_id: str
    buyer_id:        str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/conversations/start", status_code=201)
async def start_conversation(body: StartConversationIn, db: AsyncSession = Depends(get_db)):
    """بدء محادثة بين مشتري وبائع."""
    result  = await db.execute(select(Listing).where(Listing.id == uuid.UUID(body.listing_id)))
    listing = result.scalar_one_or_none()
    if not listing or listing.status != ListingStatus.published:
        raise HTTPException(404, "الإعلان غير موجود أو غير منشور")

    # Check existing conversation
    existing = (await db.execute(
        select(Conversation).where(and_(
            Conversation.listing_id == uuid.UUID(body.listing_id),
            Conversation.buyer_id   == uuid.UUID(body.buyer_id),
        ))
    )).scalar_one_or_none()

    if existing:
        return {"conversation_id": str(existing.id), "disclaimer_signed": existing.disclaimer_signed}

    conv = Conversation(
        id=uuid.uuid4(),
        listing_id=uuid.UUID(body.listing_id),
        buyer_id=uuid.UUID(body.buyer_id),
        seller_id=listing.seller_id,
        disclaimer_signed=False,
    )
    db.add(conv)
    await db.commit()
    return {"conversation_id": str(conv.id), "disclaimer_signed": False}


@router.post("/conversations/sign-disclaimer")
async def sign_disclaimer(body: SignDisclaimerIn, db: AsyncSession = Depends(get_db)):
    """
    المشتري يوقّع الإقرار بأن المنصة غير مسؤولة عن
    أي دفع قبل المعاينة الفعلية.
    """
    result = (await db.execute(
        select(Conversation).where(and_(
            Conversation.id       == uuid.UUID(body.conversation_id),
            Conversation.buyer_id == uuid.UUID(body.buyer_id),
        ))
    )).scalar_one_or_none()
    if not result:
        raise HTTPException(404, "المحادثة غير موجودة")

    result.disclaimer_signed    = True
    result.disclaimer_signed_at = datetime.utcnow()
    await db.commit()
    return {"status": "signed", "can_chat": True}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

    return [
        {
            "id":         str(m.id),
            "sender_id":  str(m.sender_id),
            "content":    m.content,
            "is_read":    m.is_read,
            "filtered":   m.was_filtered,
            "created_at": m.created_at.isoformat(),
        }
        for m in rows
    ]


@router.websocket("/ws/{conversation_id}/{user_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    WebSocket للمحادثة الفورية.
    يتحقق من توقيع الإقرار ويفلتر بيانات التواصل الخارجية.
    """
    await manager.connect(conversation_id, websocket)
    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)
            text = data.get("message", "").strip()
            if not text:
                continue

            # Load conversation
            conv = (await db.execute(
                select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
            )).scalar_one_or_none()

            if not conv or not conv.disclaimer_signed:
                await websocket.send_json({
                    "type":    "error",
                    "message": "يجب توقيع الإقرار أولاً",
                })
                continue

            cleaned, was_filtered = _sanitize(text)

            if was_filtered:
                await websocket.send_json({
                    "type":    "warning",
                    "message": "⚠️ تم حذف بيانات التواصل الخارجية. يُمنع تبادل أرقام الهاتف أو وسائل التواصل خارج المنصة.",
                })

            msg = Message(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                sender_id=uuid.UUID(user_id),
                content=cleaned,
                was_filtered=was_filtered,
            )
            db.add(msg)
            await db.commit()

            await manager.broadcast(conversation_id, {
                "type":       "message",
                "id":         str(msg.id),
                "sender_id":  user_id,
                "content":    cleaned,
                "filtered":   was_filtered,
                "created_at": msg.created_at.isoformat(),
            })

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
