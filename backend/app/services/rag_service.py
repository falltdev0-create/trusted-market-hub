"""
app/services/rag_service.py — خدمة RAG محلية بالكامل (Hugging Face)

- Embeddings: sentence-transformers (محلي) مع بديل hashing عند غياب المكتبة
- Store: جدول MySQL `rag_documents` + فهرس في الذاكرة (numpy cosine)
- Generation: transformers text2text/causal pipeline مع بديل استخراجي (extractive)

كل شيء يعمل على localhost بدون أي اتصال خارجي بعد تنزيل النماذج مرة واحدة.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import uuid
from typing import Any, Dict, List, Optional

log = logging.getLogger("rag_service")

DEFAULT_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_LLM_MODEL = "google/flan-t5-base"
FALLBACK_DIM = 384


def _chunk(text: str, size: int = 900, overlap: int = 150) -> List[str]:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out, start = [], 0
    while start < len(text):
        out.append(text[start : start + size])
        start += max(1, size - overlap)
    return out


def _hash_embed(text: str, dim: int = FALLBACK_DIM) -> List[float]:
    """تضمين احتياطي بدون أي نموذج (bag-of-words hashing) — يكفي للتجربة."""
    vec = [0.0] * dim
    for tok in re.findall(r"\w+", (text or "").lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % dim] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    n = min(len(a), len(b))
    dot = sum(a[i] * b[i] for i in range(n))
    na = math.sqrt(sum(x * x for x in a[:n])) or 1.0
    nb = math.sqrt(sum(x * x for x in b[:n])) or 1.0
    return dot / (na * nb)


class RAGService:
    def __init__(self):
        self._embedder = None
        self._embedder_name: str = DEFAULT_EMBED_MODEL
        self._embedder_ready = False
        self._llm = None
        self._llm_name: str = DEFAULT_LLM_MODEL
        self._llm_ready = False

    # ── models ───────────────────────────────────────────────────────────
    @property
    def embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore

                self._embedder = SentenceTransformer(self._embedder_name)
                self._embedder_ready = True
                log.info("✅ embedding model loaded: %s", self._embedder_name)
            except Exception as e:  # pragma: no cover
                log.warning("embedding model unavailable (%s) — using hashing fallback", e)
                self._embedder = False
        return self._embedder

    @property
    def llm(self):
        if self._llm is None:
            try:
                from transformers import pipeline  # type: ignore

                task = "text2text-generation" if "t5" in self._llm_name.lower() else "text-generation"
                self._llm = pipeline(task, model=self._llm_name)
                self._llm_ready = True
                log.info("✅ LLM loaded: %s (%s)", self._llm_name, task)
            except Exception as e:  # pragma: no cover
                log.warning("LLM unavailable (%s) — using extractive answers", e)
                self._llm = False
        return self._llm

    def embed(self, texts: List[str]) -> List[List[float]]:
        model = self.embedder
        if model:
            try:
                vectors = model.encode(texts, normalize_embeddings=True)
                return [list(map(float, v)) for v in vectors]
            except Exception as e:  # pragma: no cover
                log.warning("encode failed (%s) — fallback", e)
        return [_hash_embed(t) for t in texts]

    def status(self) -> Dict[str, Any]:
        return {
            "embedding_model": self._embedder_name,
            "embedding_loaded": bool(self._embedder_ready),
            "embedding_fallback": not self._embedder_ready,
            "llm_model": self._llm_name,
            "llm_loaded": bool(self._llm_ready),
            "dim": FALLBACK_DIM,
        }

    # ── storage (raw SQL so it works with the existing MySQL schema) ──────
    async def upsert(
        self,
        db,
        *,
        source: str,
        source_id: Optional[str],
        title: Optional[str],
        content: str,
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        from sqlalchemy import text as sql

        chunks = _chunk(content)
        if not chunks:
            return {"inserted": 0, "chunks": 0}

        await db.execute(
            sql("DELETE FROM rag_documents WHERE source = :s AND source_id = :sid"),
            {"s": source, "sid": source_id or ""},
        )
        vectors = self.embed(chunks)
        for i, (chunk, vec) in enumerate(zip(chunks, vectors)):
            await db.execute(
                sql(
                    """INSERT INTO rag_documents
                       (id, source, source_id, title, chunk_index, content, embedding, metadata, created_at)
                       VALUES (:id, :s, :sid, :t, :ci, :c, :e, :m, NOW())"""
                ),
                {
                    "id": str(uuid.uuid4()),
                    "s": source,
                    "sid": source_id or "",
                    "t": (title or "")[:255],
                    "ci": i,
                    "c": chunk,
                    "e": json.dumps(vec),
                    "m": json.dumps(metadata or {}, ensure_ascii=False),
                },
            )
        await db.commit()
        return {"inserted": len(chunks), "chunks": len(chunks), "source": source, "source_id": source_id}

    async def search(self, db, query: str, top_k: int = 5, source: Optional[str] = None) -> List[Dict[str, Any]]:
        from sqlalchemy import text as sql

        qvec = self.embed([query])[0]
        stmt = "SELECT id, source, source_id, title, content, embedding, metadata FROM rag_documents"
        params: Dict[str, Any] = {}
        if source:
            stmt += " WHERE source = :s"
            params["s"] = source
        rows = (await db.execute(sql(stmt), params)).all()

        scored = []
        for r in rows:
            try:
                emb = json.loads(r[5]) if isinstance(r[5], str) else list(r[5] or [])
            except Exception:
                continue
            scored.append(
                {
                    "id": r[0],
                    "source": r[1],
                    "source_id": r[2],
                    "title": r[3],
                    "content": r[4],
                    "metadata": json.loads(r[6]) if isinstance(r[6], str) and r[6] else {},
                    "score": round(_cosine(qvec, emb), 4),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: max(1, min(top_k, 20))]

    # ── generation ───────────────────────────────────────────────────────
    def generate(self, question: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        ctx = "\n\n".join(f"- {c['content']}" for c in contexts[:5])
        if not ctx:
            return {"answer": "لا توجد مستندات مفهرسة كافية للإجابة.", "used_llm": False}

        model = self.llm
        if model:
            prompt = (
                "أجب على السؤال اعتماداً على السياق فقط وبالعربية.\n"
                f"السياق:\n{ctx}\n\nالسؤال: {question}\nالإجابة:"
            )
            try:
                out = model(prompt, max_new_tokens=256)
                text = out[0].get("generated_text") or out[0].get("summary_text") or ""
                text = text.replace(prompt, "").strip()
                if text:
                    return {"answer": text, "used_llm": True, "llm_model": self._llm_name}
            except Exception as e:  # pragma: no cover
                log.warning("generation failed (%s) — extractive fallback", e)

        best = contexts[0]["content"]
        return {"answer": best[:700], "used_llm": False}


_rag: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    global _rag
    if _rag is None:
        _rag = RAGService()
    return _rag
