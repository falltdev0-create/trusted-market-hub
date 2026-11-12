"""
app/services/ai_service.py — Unified AI service that delegates to ai_models/
Wraps ConditionPredictor, DocumentMatcher, and PricingPredictor with async helpers,
graceful fallbacks, and no hard failure on missing weights (returns heuristic results).
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import asyncio
import io
import logging

from app.core.config import settings
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _abs(p: str) -> str:
    q = Path(p)
    return str(q if q.is_absolute() else _ROOT / q)

log = logging.getLogger("ai_service")


class AIService:
    """Facade over the underlying HuggingFace-backed predictors in ai_models/."""

    def __init__(self):
        self._condition = None
        self._document = None
        self._pricing = None
        # نموذج ثقيل واحد في كل مرة (condition + document) لمنع تراكم الذاكرة
        self._heavy_sem = asyncio.Semaphore(1)

    # ── lazy loaders ─────────────────────────────────────────────────────
    @property
    def condition(self):
        if self._condition is None:
            try:
                from ai_models.condition_model.predictor import ConditionPredictor
                self._condition = ConditionPredictor(_abs(settings.CONDITION_MODEL_PATH))
                log.info("✅ ConditionPredictor loaded")
            except Exception as e:
                log.warning("Condition model unavailable, using heuristic: %s", e)
                self._condition = _HeuristicCondition()
        return self._condition

    @property
    def document(self):
        if self._document is None:
            try:
                from ai_models.document_model.predictor import DocumentMatcher
                self._document = DocumentMatcher()
                log.info("✅ DocumentMatcher loaded")
            except Exception as e:
                log.warning("Document model unavailable, using heuristic: %s", e)
                self._document = _HeuristicDocument()
        return self._document

    @property
    def pricing(self):
        if self._pricing is None:
            try:
                from ai_models.pricing_model.predictor import PricingPredictor
                self._pricing = PricingPredictor(_abs(settings.PRICING_MODEL_PATH))
                log.info("✅ PricingPredictor loaded")
            except Exception as e:
                log.warning("Pricing model unavailable, using heuristic: %s", e)
                self._pricing = _HeuristicPricing()
        return self._pricing

    # ── public async API ─────────────────────────────────────────────────
    async def assess_condition(
        self,
        images: List[bytes] | str,
        category: str = "house",
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        # Backwards compat: some callers pass a URL string
        if isinstance(images, str):
            image_bytes = await _fetch_bytes(images)
            images = [image_bytes] if image_bytes else []
        async with self._heavy_sem:
            result = await loop.run_in_executor(
                None, self.condition.predict, images, category
            )
        # normalize: الواجهة تتوقع 0..1 (النموذج الحقيقي يرجع 10..100)
        score = float(result.get("score", 0.5))
        if score > 1.0:
            score /= 100.0
        return {
            "grade": result.get("grade", "good"),
            "score": score,
            "report": result.get("report") or result,
            "model": getattr(self.condition, "model_name", "heuristic"),
            "needs_review": bool(result.get("needs_review", False)),
        }

    async def verify_document(
        self,
        document_url: str,
        document_type: str = "ownership",
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        async with self._heavy_sem:
            result = await loop.run_in_executor(
                None, self.document.verify, document_url, document_type
            )
        return {
            "match_status": result.get("match_status", "pending"),
            "match_score": float(result.get("match_score", 0.0)),
            "extracted_text": result.get("extracted_text"),
            "model": getattr(self.document, "model_name", "heuristic"),
        }

    async def match_documents(
        self,
        id_doc_bytes: bytes,
        ownership_doc_bytes: bytes,
        category: str = "house",
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        async with self._heavy_sem:
            result = await loop.run_in_executor(
                None, self.document.match, id_doc_bytes, ownership_doc_bytes, category
            )
        return result

    async def estimate_price(
        self,
        category: str,
        listing_type: str,
        condition_grade: str,
        features: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return {suggested_min, suggested_max, market_avg, tier, confidence}."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.pricing.predict,
            category, listing_type, condition_grade, features or {},
        )
        return result

    def classify_tier(self, price: float, category: str) -> str:
        """Deterministic tier classification against settings.PRICE_TIERS."""
        tiers = getattr(settings, "PRICE_TIERS", None) or _DEFAULT_TIER_THRESHOLDS
        t = tiers.get(category) or tiers.get("other") or {"cheap": 100_000, "medium": 500_000}
        if price <= t["cheap"]:
            return "cheap"
        if price <= t["medium"]:
            return "medium"
        return "expensive"


# ═════════════════════════════ heuristic fallbacks ═════════════════════════
_DEFAULT_TIER_THRESHOLDS = {
    "house":    {"cheap": 2_000_000, "medium": 5_000_000},
    "property": {"cheap": 2_000_000, "medium": 5_000_000},
    "car":      {"cheap":   800_000, "medium": 2_000_000},
    "other":    {"cheap":    50_000, "medium":   250_000},
}


class _HeuristicCondition:
    """يعمل فقط عند غياب الأوزان: درجة محايدة مع علامة مراجعة (وليس تقديراً مبنياً على عدد الصور)."""
    model_name = "unavailable-condition"

    def predict(self, images, category="house"):
        return {
            "grade": "good",
            "score": 0.5,
            "needs_review": True,
            "report": {"note": "نموذج التقييم غير متاح — يلزم تقييم المشرف"},
        }


class _HeuristicDocument:
    """fail-closed: غياب النموذج لا يعني القبول أبداً."""
    model_name = "unavailable-document"

    def verify(self, url: str, doc_type: str = "ownership"):
        return {"match_status": "pending", "match_score": 0.0, "extracted_text": None}

    def match(self, id_bytes, ownership_bytes, category="house"):
        return {
            "match_score": 0.0,
            "passed": False,
            "needs_manual_review": True,
            "matched_fields": {},
            "issues": ["نموذج المطابقة غير متاح — تحويل للمراجعة اليدوية"],
        }


class _HeuristicPricing:
    model_name = "heuristic-pricing"

    def predict(self, category, listing_type, condition_grade, features):
        base = {"house": 1_500_000, "property": 1_500_000, "car": 1_500_000, "other": 100_000}.get(category, 500_000)
        cond_mult = {"excellent": 1.4, "good": 1.0, "fair": 0.75, "poor": 0.5}.get(condition_grade, 1.0)
        type_mult = 0.02 if listing_type == "rent" else 1.0
        mid = int(base * cond_mult * type_mult)
        lo, hi = int(mid * 0.7), int(mid * 1.4)
        tiers = _DEFAULT_TIER_THRESHOLDS.get(category, _DEFAULT_TIER_THRESHOLDS["other"])
        tier = "cheap" if mid <= tiers["cheap"] else "medium" if mid <= tiers["medium"] else "expensive"
        return {
            "suggested_min": lo,
            "suggested_max": hi,
            "market_avg": mid,
            "tier": tier,
            "confidence": 0.6,
        }


async def _fetch_bytes(url: str) -> Optional[bytes]:
    try:
        import requests
        r = requests.get(url, timeout=8)
        return r.content if r.ok else None
    except Exception:
        return None


# Singleton
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service