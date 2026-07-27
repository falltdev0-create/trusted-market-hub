"""
AI Service — خدمة الذكاء الاصطناعي
ينسق استدعاء نماذج التقييم والمطابقة والتسعير
"""

from typing import List
import asyncio
import io

from app.core.config import settings


class AIService:
    """
    واجهة موحدة لنماذج الذكاء الاصطناعي.
    كل نموذج يعمل بشكل مستقل ويمكن استبداله بنموذج أحدث.
    """

    def __init__(self):
        self._condition_model = None
        self._doc_model       = None
        self._pricing_model   = None

    @property
    def condition_model(self):
        if self._condition_model is None:
            from ai_models.condition_model.predictor import ConditionPredictor
            self._condition_model = ConditionPredictor(settings.CONDITION_MODEL_PATH)
        return self._condition_model

    @property
    def doc_model(self):
        if self._doc_model is None:
            from ai_models.document_model.predictor import DocumentMatcher
            self._doc_model = DocumentMatcher()
        return self._doc_model

    @property
    def pricing_model(self):
        if self._pricing_model is None:
            from ai_models.pricing_model.predictor import PricingPredictor
            self._pricing_model = PricingPredictor(settings.PRICING_MODEL_PATH)
        return self._pricing_model

    async def assess_condition(
        self,
        images: List[bytes],
        category: str,
    ) -> dict:
        """
        تقييم حالة السلعة من مجموعة صور.
        Returns: {grade, score, report}
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.condition_model.predict,
            images,
            category,
        )
        return result

    async def match_documents(
        self,
        id_doc_bytes: bytes,
        ownership_doc_bytes: bytes,
        category: str,
    ) -> dict:
        """
        مطابقة وثيقة الهوية مع وثيقة الملكية.
        Returns: {match_score, matched_fields, issues}
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.doc_model.match,
            id_doc_bytes,
            ownership_doc_bytes,
            category,
        )
        return result

    async def estimate_price(
        self,
        category: str,
        listing_type: str,
        condition_grade: str,
        features: dict,
    ) -> dict:
        """
        تقدير السعر المناسب وفق السوق.
        Returns: {suggested_price, price_range, confidence}
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.pricing_model.predict,
            category,
            listing_type,
            condition_grade,
            features,
        )
        return result
