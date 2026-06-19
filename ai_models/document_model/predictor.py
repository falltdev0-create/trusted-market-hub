"""
مطابقة وثائق الملكية مع الهوية v2

المنهجية:
  • OCR: EasyOCR (عربي+إنجليزي) + Tesseract احتياطي
  • استخراج الاسم + الأرقام من كلا الوثيقتين
  • مطابقة مرنة: Levenshtein + Arabic normalization
  • نتيجة مجمّعة: اسم 60% + أرقام 40%
  • حد القبول: 70 نقطة
"""

import io
import re
from typing import Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════════════
# Arabic Text Normalizer
# ══════════════════════════════════════════════════════════════════════════════

class ArabicNormalizer:
    _ALEF      = re.compile(r'[إأآا]')
    _YA        = re.compile(r'[يى]')
    _TA        = re.compile(r'ة')
    _DIAC      = re.compile(r'[\u064B-\u065F\u0670]')
    _TATWEEL   = re.compile(r'\u0640')
    _SPACES    = re.compile(r'\s+')

    @classmethod
    def normalize(cls, text: str) -> str:
        text = cls._DIAC.sub('', text)
        text = cls._TATWEEL.sub('', text)
        text = cls._ALEF.sub('ا', text)
        text = cls._YA.sub('ي', text)
        text = cls._TA.sub('ه', text)
        return cls._SPACES.sub(' ', text).strip()

    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        latin = text.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))
        return re.findall(r'\d{4,}', latin)


# ══════════════════════════════════════════════════════════════════════════════
# Similarity
# ══════════════════════════════════════════════════════════════════════════════

def _levenshtein(s1: str, s2: str) -> float:
    if not s1 and not s2: return 1.0
    if not s1 or  not s2: return 0.0
    len1, len2 = len(s1), len(s2)
    dp = list(range(len2 + 1))
    for i in range(1, len1 + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, len2 + 1):
            old = dp[j]
            dp[j] = min(dp[j] + 1, dp[j-1] + 1,
                        prev + (0 if s1[i-1] == s2[j-1] else 1))
            prev = old
    return 1.0 - dp[len2] / max(len1, len2)


def _name_score(n1: str, n2: str) -> float:
    norm = ArabicNormalizer.normalize
    w1, w2 = norm(n1).split(), norm(n2).split()
    if not w1 or not w2: return 0.0
    scores   = [max(_levenshtein(w, x) for x in w2) for w in w1]
    coverage = sum(1 for s in scores if s > 0.75) / len(scores)
    return float(sum(scores) / len(scores) * 0.6 + coverage * 0.4)


def _number_score(nums1: List[str], nums2: List[str]) -> float:
    if not nums1 or not nums2: return 0.0
    for n1 in nums1:
        for n2 in nums2:
            if n1 == n2: return 1.0
            if len(n1) >= 8 and len(n2) >= 8 and n1[-8:] == n2[-8:]:
                return 0.85
    return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# OCR Engine
# ══════════════════════════════════════════════════════════════════════════════

class _OCR:
    _reader = None

    @classmethod
    def _get_reader(cls):
        if cls._reader is None:
            try:
                import easyocr
                cls._reader = easyocr.Reader(['ar', 'en'], gpu=False, verbose=False)
            except ImportError:
                cls._reader = "unavailable"
        return cls._reader

    @classmethod
    def extract(cls, img_bytes: bytes) -> str:
        from PIL import Image
        try:
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        except Exception:
            return ""

        reader = cls._get_reader()
        if reader != "unavailable":
            try:
                import numpy as np
                results = reader.readtext(np.array(img), detail=0)
                return " ".join(results)
            except Exception:
                pass

        # Fallback: Tesseract
        try:
            import pytesseract
            return pytesseract.image_to_string(img, lang="ara+eng")
        except Exception:
            return ""


# ══════════════════════════════════════════════════════════════════════════════
# Document Matcher
# ══════════════════════════════════════════════════════════════════════════════

class DocumentMatcher:
    PASS_THRESHOLD = 70.0

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        print("✅ DocumentMatcher v2 initialized")

    def match(
        self,
        id_doc_bytes: bytes,
        ownership_doc_bytes: bytes,
        category: str = "house",
    ) -> Dict:
        id_text  = _OCR.extract(id_doc_bytes)
        own_text = _OCR.extract(ownership_doc_bytes)

        id_name  = self._extract_name(id_text)
        own_name = self._extract_name(own_text)
        id_nums  = ArabicNormalizer.extract_numbers(id_text)
        own_nums = ArabicNormalizer.extract_numbers(own_text)

        name_score   = _name_score(id_name, own_name) * 100
        number_score = _number_score(id_nums, own_nums) * 100
        match_score  = round(name_score * 0.60 + number_score * 0.40, 1)

        issues = []
        if name_score   < 60: issues.append(f"الاسم غير متطابق — هوية: '{id_name}' | ملكية: '{own_name}'")
        if number_score < 50: issues.append("الأرقام (هوية/تسجيل) غير متطابقة")
        if not id_name:       issues.append("تعذّر استخراج الاسم من وثيقة الهوية")
        if not own_name:      issues.append("تعذّر استخراج الاسم من وثيقة الملكية")

        return {
            "match_score":    match_score,
            "passed":         match_score >= self.PASS_THRESHOLD,
            "name_score":     round(name_score, 1),
            "number_score":   round(number_score, 1),
            "matched_fields": {
                "id_name":     id_name,
                "own_name":    own_name,
                "id_numbers":  id_nums[:3],
                "own_numbers": own_nums[:3],
            },
            "issues":         issues,
            "model_version":  "v2-easyocr-levenshtein",
        }

    @staticmethod
    def _extract_name(text: str) -> str:
        norm = ArabicNormalizer.normalize(text)
        m = re.search(r'(?:الاسم|الاسم الكامل|اسم المالك)[:\s]+([^\n\d،,]{5,60})', norm)
        if m:
            return m.group(1).strip()
        for line in norm.splitlines():
            words = [w for w in line.split() if re.match(r'^[\u0600-\u06FF]{3,}$', w)]
            if 2 <= len(words) <= 6:
                return " ".join(words)
        return ""
