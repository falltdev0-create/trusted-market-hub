"""
app/services/ai_service.py — منسق نماذج الذكاء الاصطناعي
تقييم الحالة | مطابقة الوثائق | تقدير السعر
Lazy loading — النماذج تُحمّل عند الاستدعاء الأول فقط
"""

import asyncio
from typing import List
from functools import cached_property

from app.core.config import settings


class AIService:

    @cached_property
    def condition_model(self):
        from ai_models.condition_model.predictor import ConditionPredictor
        return ConditionPredictor(settings.CONDITION_MODEL_PATH)

    @cached_property
    def document_model(self):
        from ai_models.document_model.predictor import DocumentMatcher
        return DocumentMatcher(settings.DOCUMENT_MODEL_PATH)

    @cached_property
    def pricing_model(self):
        from ai_models.pricing_model.predictor import PricingPredictor
        return PricingPredictor(settings.PRICING_MODEL_PATH)

    async def assess_condition(self, images: List[bytes], category: str) -> dict:
        """
        تقييم حالة السلعة من صور متعددة.
        → {grade, grade_ar, score, confidence, uncertainty, criteria_scores, recommendations}
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.condition_model.predict, images, category
        )

    async def match_documents(
        self,
        id_doc_bytes: bytes,
        ownership_doc_bytes: bytes,
        category: str,
    ) -> dict:
        """
        مطابقة بطاقة الهوية مع وثيقة الملكية.
        → {match_score, passed, name_score, number_score, matched_fields, issues}
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.document_model.match,
            id_doc_bytes, ownership_doc_bytes, category
        )

    async def estimate_price(
        self,
        category: str,
        listing_type: str,
        condition_grade: str,
        features: dict,
    ) -> dict:
        """
        تقدير السعر المناسب وفق السوق.
        → {suggested_price, price_range, confidence, method}
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.pricing_model.predict,
            category, listing_type, condition_grade, features
        )


# Singleton
ai_service = AIService()
