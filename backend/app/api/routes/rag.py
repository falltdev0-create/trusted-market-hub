"""
app/api/routes/rag.py — واجهات RAG للتجربة والتشغيل المحلي

POST   /api/v1/rag/index            إضافة/تحديث مستند نصي في الفهرس (مشرف)
POST   /api/v1/rag/index/listings   فهرسة كل الإعلانات المنشورة (مشرف)
POST   /api/v1/rag/search           بحث دلالي فقط (بدون توليد)
POST   /api/v1/rag/ask              سؤال + إجابة مع المصادر (RAG كامل)
GET    /api/v1/rag/status           حالة النماذج وعدد المستندات
DELETE /api/v1/rag/documents/{id}   حذف مستند (مشرف)
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text as sql
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.core.security import require_admin_role
from app.models.models import User
from app.services.rag_service import get_rag_service

router = APIRouter()


class IndexIn(BaseModel):
    source: str = "faq"
    source_id: Optional[str] = None
    title: Optional[str] = None
    content: str
    metadata: Optional[dict] = None


class SearchIn(BaseModel):
    query: str
    top_k: int = 5
    source: Optional[str] = None


class AskIn(BaseModel):
    question: str
    top_k: int = 5
    source: Optional[str] = None


@router.get("/status")
async def rag_status(db: AsyncSession = Depends(get_db)):
    rag = get_rag_service()
    try:
        total = (await db.execute(sql("SELECT COUNT(*) FROM rag_documents"))).scalar() or 0
        by_source = [
            {"source": r[0], "count": r[1]}
            for r in (await db.execute(sql("SELECT source, COUNT(*) FROM rag_documents GROUP BY source"))).all()
        ]
    except Exception:
        total, by_source = 0, []
    return {"ok": True, **rag.status(), "documents": total, "by_source": by_source}


@router.post("/index")
async def rag_index(
    body: IndexIn,
    _admin: User = Depends(require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    if not body.content.strip():
        raise HTTPException(400, "المحتوى فارغ")
    rag = get_rag_service()
    return await rag.upsert(
        db,
        source=body.source,
        source_id=body.source_id,
        title=body.title,
        content=body.content,
        metadata=body.metadata,
    )


@router.post("/index/listings")
async def rag_index_listings(
    _admin: User = Depends(require_admin_role("moderator")),
    db: AsyncSession = Depends(get_db),
):
    rag = get_rag_service()
    rows = (await db.execute(sql(
        """SELECT id, title, description, city, district, category, listing_type,
                  price, price_tier, condition_grade
           FROM listings WHERE status = 'published' LIMIT 500"""
    ))).all()
    indexed = 0
    for r in rows:
        content = (
            f"العنوان: {r[1] or ''}. الوصف: {r[2] or ''}. المدينة: {r[3] or ''} {r[4] or ''}. "
            f"الفئة: {r[5] or ''} - {r[6] or ''}. السعر: {r[7] or 'غير محدد'} ({r[8] or 'غير مصنف'}). "
            f"الحالة: {r[9] or 'غير محددة'}."
        )
        await rag.upsert(
            db,
            source="listing",
            source_id=str(r[0]),
            title=r[1],
            content=content,
            metadata={"city": r[3], "category": r[5], "price": float(r[7]) if r[7] else None, "tier": r[8]},
        )
        indexed += 1
    return {"indexed_listings": indexed}


@router.post("/search")
async def rag_search(
    body: SearchIn,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.query.strip():
        raise HTTPException(400, "أدخل نص البحث")
    rag = get_rag_service()
    results = await rag.search(db, body.query, body.top_k, body.source)
    return {"query": body.query, "results": results}


@router.post("/ask")
async def rag_ask(
    body: AskIn,
    _user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not body.question.strip():
        raise HTTPException(400, "أدخل السؤال")
    rag = get_rag_service()
    contexts = await rag.search(db, body.question, body.top_k, body.source)
    result = rag.generate(body.question, contexts)
    return {
        "question": body.question,
        **result,
        "sources": [
            {"id": c["id"], "source": c["source"], "source_id": c["source_id"], "title": c["title"], "score": c["score"]}
            for c in contexts
        ],
    }


@router.delete("/documents/{doc_id}")
async def rag_delete(
    doc_id: str,
    _admin: User = Depends(require_admin_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(sql("DELETE FROM rag_documents WHERE id = :id"), {"id": doc_id})
    await db.commit()
    return {"deleted": doc_id}
