"""
نموذج تقدير السعر v1

ML: XGBoost (يُدرّب على بيانات السوق السوداني)
Fallback: جداول أسعار ثابتة إذا لم يُوجد النموذج
"""

import os
from typing import Dict, Optional


PRICE_TABLES = {
    "house": {
        "sale": {
            "excellent": {"base": 1_500_000, "per_m2": 4_500},
            "good":      {"base":   900_000, "per_m2": 2_800},
            "poor":      {"base":   450_000, "per_m2": 1_500},
        },
        "rent": {
            "excellent": {"base": 25_000, "per_m2": 80},
            "good":      {"base": 15_000, "per_m2": 50},
            "poor":      {"base":  8_000, "per_m2": 28},
        },
    },
    "car": {
        "sale": {
            "excellent": {"base_per_year": 180_000, "km_penalty": 1.2},
            "good":      {"base_per_year": 120_000, "km_penalty": 1.5},
            "poor":      {"base_per_year":  70_000, "km_penalty": 2.0},
        },
        "rent": {
            "excellent": {"per_day": 8_000},
            "good":      {"per_day": 5_500},
            "poor":      {"per_day": 3_500},
        },
    },
}

CITY_MULT = {
    "الخرطوم": 1.00, "بحري": 0.95, "أم درمان": 0.90,
    "بورتسودان": 0.85, "ودمدني": 0.80, "كسلا": 0.75, "الأبيض": 0.75,
}

CURRENT_YEAR = 2025


class PricingPredictor:

    def __init__(self, model_path: Optional[str] = None):
        self._model   = None
        self._encoder = None
        self._use_ml  = False

        if model_path and os.path.exists(model_path):
            try:
                import joblib
                bundle        = joblib.load(model_path)
                self._model   = bundle["model"]
                self._encoder = bundle.get("encoder")
                self._use_ml  = True
                print("✅ PricingPredictor: ML model loaded")
            except Exception as e:
                print(f"⚠️ PricingPredictor fallback to tables — {e}")
        else:
            print("ℹ️ PricingPredictor: using static price tables")

    def predict(
        self,
        category:        str,
        listing_type:    str,
        condition_grade: str,
        features:        dict,
    ) -> Dict:
        if self._use_ml:
            return self._ml(category, listing_type, condition_grade, features)
        return self._table(category, listing_type, condition_grade, features)

    def _ml(self, category, listing_type, condition_grade, features) -> Dict:
        import numpy as np
        row = [category, listing_type, condition_grade,
               features.get("city", "الخرطوم"),
               features.get("size", 100), features.get("bedrooms", 3),
               features.get("year", 2015), features.get("km", 50_000)]
        X    = self._encoder.transform([row])
        pred = float(self._model.predict(X)[0])
        std  = pred * 0.12
        return {
            "suggested_price": round(pred, -3),
            "price_range":     (round(pred - std, -3), round(pred + std, -3)),
            "confidence":      0.82,
            "method":          "xgboost",
        }

    def _table(self, category, listing_type, condition_grade, features) -> Dict:
        try:
            t = PRICE_TABLES[category][listing_type][condition_grade]
        except KeyError:
            return {"suggested_price": 0, "price_range": (0, 0), "confidence": 0.0, "method": "fallback"}

        city_m = CITY_MULT.get(features.get("city", "الخرطوم"), 0.85)

        if category == "house":
            price = t["base"] + features.get("size", 100) * t["per_m2"]
        elif category == "car" and listing_type == "sale":
            age   = max(1, CURRENT_YEAR - features.get("year", 2015))
            km    = features.get("km", 50_000)
            price = max(t["base_per_year"] * (10 - min(age, 9)) - km * t["km_penalty"], 50_000)
        elif category == "car" and listing_type == "rent":
            price = t["per_day"] * 30
        else:
            price = 0

        price  *= city_m
        spread  = price * 0.15
        return {
            "suggested_price": round(price, -3),
            "price_range":     (round(price - spread, -3), round(price + spread, -3)),
            "confidence":      0.65,
            "method":          "static_table",
        }
