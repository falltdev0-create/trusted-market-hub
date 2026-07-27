"""
Chat Routes — مسارات المحادثة
WebSocket داخلي فقط — يمنع تبادل بيانات التواصل الخارجية
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime
import uuid
import re
import json

from app.core.database import get_db
from app.models.listing import Conversation, Message, Listing, ListingStatus, User
from pydantic import BaseModel

router = APIRouter()


# ── Contact-info filter ───────────────────────────────────────────────────────

CONTACT_PATTERNS = [
    # Phone numbers (various formats)
    r'\b\+?[\d\s\-\(\)]{9,15}\b',
    # Email addresses
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
    # WhatsApp / Telegram mentions
    r'\b(whatsapp|واتساب|تيليجرام|telegram|snapchat|سناب|انستا|instagram)\b',
    # Social media @ handles
    r'@[a-zA-Z0-9_]{3,30}',
]

CONTACT_REGEX = re.compile(
    '|'.join(CONTACT_PATTERNS),
    re.IGNORECASE | re.UNICODE
)


def sanitize_message(text: str) -> tuple[str, bool]:
    """
    Returns (sanitized_text, was_filtered).
    Replaces contact info with *** to block external communication.
    """
    found = CONTACT_REGEX.search(text)
    if found:
        cleaned = CONTACT_REGEX.sub("***", text)
        return cleaned, True
    return text, False


# ── Schemas ──────────────────────────────────────────────────────────────────

class StartConversationRequest(BaseModel):
    listing_id: str
    buyer_id: str


class SignDisclaimerRequest(BaseModel):
    conversation_id: str
    buyer_id: str


# ── WebSocket Manager (in-memory for single instance; use Redis pub/sub for multi-node) ──

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, conversation_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(conversation_id, []).append(ws)

    def disconnect(self, conversation_id: str, ws: WebSocket):
        if conversation_id in self.active:
            self.active[conversation_id].discard(ws)

    async def broadcast(self, conversation_id: str, data: dict):
        for ws in self.active.get(conversation_id, []):
            try:
                await ws.send_json(data)
            except Exception:
                pass


manager = ConnectionManager()


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/conversations/start", status_code=201)
async def start_conversation(
    body: StartConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    """يبدأ محادثة بين مشتري وبائع — يشترط توقيع الإقرار أولاً"""
    listing_result = await db.execute(
        select(Listing).where(Listing.id == uuid.UUID(body.listing_id))
    )
    listing = listing_result.scalar_one_or_none()
    if not listing or listing.status != ListingStatus.published:
        raise HTTPException(status_code=404, detail="الإعلان غير موجود أو غير منشور")

    # Check if conversation exists
    existing = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.listing_id == uuid.UUID(body.listing_id),
                Conversation.buyer_id == uuid.UUID(body.buyer_id),
            )
        )
    )
    conv = existing.scalar_one_or_none()
    if conv:
        return {"conversation_id": str(conv.id), "disclaimer_signed": conv.disclaimer_signed}

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
async def sign_disclaimer(
    body: SignDisclaimerRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    المشتري يوقّع على الإقرار بأن المنصة غير مسؤولة
    عن الدفع قبل المعاينة.
    """
    result = await db.execute(
        select(Conversation).where(
            and_(
                Conversation.id == uuid.UUID(body.conversation_id),
                Conversation.buyer_id == uuid.UUID(body.buyer_id),
            )
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="المحادثة غير موجودة")

    conv.disclaimer_signed = True
    conv.disclaimer_signed_at = datetime.utcnow()
    await db.commit()

    return {"status": "signed", "can_chat": True}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    page: int = 1,
    page_size: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """جلب رسائل المحادثة (مرتبة زمنياً)"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == uuid.UUID(conversation_id))
        .order_by(Message.created_at.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    messages = result.scalars().all()
    return [
        {
            "id": str(m.id),
            "sender_id": str(m.sender_id),
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
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
    - يتحقق من توقيع الإقرار قبل السماح بالإرسال.
    - يفلتر أي بيانات تواصل خارجية (هاتف، إيميل، سوشيال ميديا).
    """
    await manager.connect(conversation_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            text = data.get("message", "").strip()

            if not text:
                continue

            # Load conversation to check disclaimer
            conv_result = await db.execute(
                select(Conversation).where(Conversation.id == uuid.UUID(conversation_id))
            )
            conv = conv_result.scalar_one_or_none()

            if not conv or not conv.disclaimer_signed:
                await websocket.send_json({
                    "type": "error",
                    "message": "يجب توقيع الإقرار أولاً قبل بدء المحادثة",
                })
                continue

            # Sanitize contact info
            cleaned_text, was_filtered = sanitize_message(text)

            if was_filtered:
                await websocket.send_json({
                    "type": "warning",
                    "message": "⚠️ تم حذف بيانات التواصل الخارجية. يُمنع تبادل أرقام الهاتف أو وسائل التواصل خارج المنصة.",
                    "original_blocked": True,
                })
                # Still save filtered version
                text = cleaned_text

            # Save to DB
            msg = Message(
                id=uuid.uuid4(),
                conversation_id=uuid.UUID(conversation_id),
                sender_id=uuid.UUID(user_id),
                content=text,
            )
            db.add(msg)
            await db.commit()

            # Broadcast to both parties
            await manager.broadcast(conversation_id, {
                "type": "message",
                "id": str(msg.id),
                "sender_id": user_id,
                "content": text,
                "created_at": msg.created_at.isoformat(),
                "filtered": was_filtered,
            })

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)
