"""
Maskan AI Models v2 — Hugging Face Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Unified interface for all Hugging Face-based models:
  • ConditionPredictor (Vision-based property/vehicle condition assessment)
  • DocumentMatcher (Arabic document verification)
  • PricingPredictor (Market-based price estimation)

استخدام:
    from ai_models_hf import ConditionPredictor, DocumentMatcher, PricingPredictor
    
    condition = ConditionPredictor()
    doc_match = DocumentMatcher()
    pricing = PricingPredictor()
"""

from .condition import ConditionPredictor
from .document import DocumentMatcher
from .pricing import PricingPredictor

__version__ = "2.0.0-hf"
__all__ = ["ConditionPredictor", "DocumentMatcher", "PricingPredictor"]
