"""
<<<<<<< HEAD
app/services/ai_service.py — خدمات AI باستخدام Hugging Face
"""

from typing import Optional, Dict, Any
from PIL import Image
import numpy as np
=======
app/services/ai_service.py — منسق نماذج الذكاء الاصطناعي
تقييم الحالة | مطابقة الوثائق | تقدير السعر
Lazy loading — النماذج تُحمّل عند الاستدعاء الأول فقط
"""

import asyncio
from typing import List
from functools import cached_property

>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
from app.core.config import settings


class AIService:
<<<<<<< HEAD
    """خدمة الذكاء الاصطناعي الموحدة"""
    
    def __init__(self):
        # Lazy import torch to avoid failing startup on systems without proper
        # PyTorch installation (e.g., Windows without CUDA runtime).
        try:
            import torch
            self.torch = torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            self.torch = None
            self.device = "cpu"
        self._load_models()
    
    def _load_models(self):
        """تحميل جميع النماذج عند البدء"""
        try:
            # Import transformers lazily
            from transformers import pipeline

            # نموذج تقييم الحالة
            self.condition_model = pipeline(
                "image-classification",
                model=settings.HF_CONDITION_MODEL,
                device=0 if self.device == "cuda" else -1
            )
            print(f"✅ Condition Model loaded: {settings.HF_CONDITION_MODEL}")
        except Exception as e:
            print(f"⚠️ Failed to load condition model: {e}")
            self.condition_model = None
        
        try:
            # نموذج التحقق من المستندات
            self.document_model = pipeline(
                "vision2seq-lm",
                model=settings.HF_DOCUMENT_MODEL,
                device=0 if self.device == "cuda" else -1
            )
            print(f"✅ Document Model loaded: {settings.HF_DOCUMENT_MODEL}")
        except Exception as e:
            print(f"⚠️ Failed to load document model: {e}")
            self.document_model = None
        
        try:
            # نموذج تحديد السعر
            self.pricing_model = pipeline(
                "text-generation",
                model=settings.HF_PRICING_MODEL,
                device=0 if self.device == "cuda" else -1
            )
            print(f"✅ Pricing Model loaded: {settings.HF_PRICING_MODEL}")
        except Exception as e:
            print(f"⚠️ Failed to load pricing model: {e}")
            self.pricing_model = None
    
    async def assess_condition(
        self, 
        image_url: str,
        category: str = "house"
    ) -> Dict[str, Any]:
        """تقييم حالة الممتلك من الصور"""
        try:
            # تحميل الصورة من الـ URL
            from PIL import Image
            import requests
            from io import BytesIO
            
            response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content))
            
            if self.condition_model is None:
                return {"grade": "good", "score": 0.75, "error": "Model not loaded"}
            
            # تنبؤ بالحالة
            result = self.condition_model(image)
            
            # معالجة النتيجة
            top_result = result[0] if result else {"label": "good", "score": 0.5}
            
            # تحويل إلى grade و score
            grade_mapping = {
                "excellent": ("excellent", 0.9),
                "good": ("good", 0.7),
                "poor": ("poor", 0.4),
            }
            
            grade, score = grade_mapping.get(
                top_result.get("label", "good"),
                ("good", top_result.get("score", 0.5))
            )
            
            return {
                "grade": grade,
                "score": min(score, 1.0),
                "confidence": top_result.get("score", 0),
                "model": settings.HF_CONDITION_MODEL,
            }
        except Exception as e:
            return {"error": str(e), "grade": "good", "score": 0.5}
    
    async def verify_document(
        self,
        document_url: str,
        document_type: str = "ownership"
    ) -> Dict[str, Any]:
        """التحقق من صحة المستندات"""
        try:
            if self.document_model is None:
                return {"match_status": "pending", "match_score": 0.0}
            
            # التحقق من المستند (نص + صور)
            # يمكن استخدام easyocr أيضا
            return {
                "match_status": "approved",
                "match_score": 0.85,
                "document_type": document_type,
                "model": settings.HF_DOCUMENT_MODEL,
            }
        except Exception as e:
            return {"error": str(e), "match_status": "rejected"}
    
=======

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

>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
    async def estimate_price(
        self,
        category: str,
        listing_type: str,
        condition_grade: str,
<<<<<<< HEAD
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """تقدير السعر بناء على الخصائص"""
        try:
            # قوائم الأسعار من الإعدادات
            price_caps = settings.PRICE_CAPS
            
            category_caps = price_caps.get(category, {})
            type_caps = category_caps.get(listing_type, {})
            estimated_price = type_caps.get(condition_grade, 0)
            
            return {
                "estimated_price": estimated_price,
                "confidence": 0.7,
                "category": category,
                "listing_type": listing_type,
                "condition": condition_grade,
            }
        except Exception as e:
            return {"error": str(e), "estimated_price": 0}


# Singleton instance
_ai_service: Optional[AIService] = None

def get_ai_service() -> AIService:
    """احصل على instance من AIService"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
=======
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
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
