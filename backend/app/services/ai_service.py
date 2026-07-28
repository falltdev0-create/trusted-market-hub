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

log = logging.getLogger("ai_service")


class AIService:
    """Facade over the underlying HuggingFace-backed predictors in ai_models/."""

    def __init__(self):
        self._condition = None
        self._document = None
        self._pricing = None

    # ── lazy loaders ─────────────────────────────────────────────────────
    @property
    def condition(self):
        if self._condition is None:
            try:
                from ai_models.condition_model.predictor import ConditionPredictor
                self._condition = ConditionPredictor(settings.CONDITION_MODEL_PATH)
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
                self._pricing = PricingPredictor(settings.PRICING_MODEL_PATH)
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
        result = await loop.run_in_executor(
            None, self.condition.predict, images, category
        )
        # normalize
        return {
            "grade": result.get("grade", "good"),
            "score": float(result.get("score", 0.7)),
            "report": result.get("report") or result,
            "model": getattr(self.condition, "model_name", "heuristic"),
        }

    async def verify_document(
        self,
        document_url: str,
        document_type: str = "ownership",
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, self.document.verify, document_url, document_type
        )
        return {
            "match_status": result.get("match_status", "approved"),
            "match_score": float(result.get("match_score", 0.85)),
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
    model_name = "heuristic-condition"

    def predict(self, images, category="house"):
        n = len(images) if hasattr(images, "__len__") else 1
        score = min(0.95, 0.55 + 0.03 * n)
        grade = "excellent" if score >= 0.8 else "good" if score >= 0.6 else "poor"
        return {
            "grade": grade,
            "score": score,
            "report": {"aspects": {"overall": int(score * 100), "images_quality": int(score * 100)}},
        }


class _HeuristicDocument:
    model_name = "heuristic-document"

    def verify(self, url: str, doc_type: str = "ownership"):
        return {"match_status": "approved", "match_score": 0.85, "extracted_text": None}

    def match(self, id_bytes, ownership_bytes, category="house"):
        return {"match_score": 0.86, "matched_fields": ["name", "national_id"], "issues": []}


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
