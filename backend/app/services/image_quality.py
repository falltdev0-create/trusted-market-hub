"""
فحص جودة صور العقار — خفيف جداً (OpenCV + numpy فقط، بلا نماذج ذكاء اصطناعي).
يرفض الصور التالفة أو الصغيرة أو الضبابية أو المظلمة/المحروقة أو المكررة قبل التخزين والتحليل.
العتبات أدناه قابلة للمعايرة حسب صور بائعيكم.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

MIN_SIDE = 480            # أقل بُعد (بكسل) للضلع الأقصر
BLUR_MIN_VARIANCE = 30.0  # تباين Laplacian على نسخة مصغّرة؛ أقل منه = ضبابية
DARK_MEAN = 35.0          # متوسط السطوع (0-255) أقل منه = مظلمة
BRIGHT_MEAN = 235.0       # أعلى منه = محروقة الإضاءة
DUP_HAMMING = 3           # أقصى فرق بتّات dHash لاعتبار صورتين مكررتين
_ANALYZE_SIDE = 800

_MESSAGES = {
    "unreadable": "الملف تالف أو ليس صورة صالحة",
    "too_small": "دقة الصورة منخفضة جداً (الحد الأدنى 480 بكسل للضلع الأقصر)",
    "blurry": "الصورة غير واضحة (ضبابية)",
    "dark": "الصورة مظلمة جداً",
    "bright": "الصورة مضيئة أكثر من اللازم",
    "duplicate": "الصورة مكررة (تشبه الصورة رقم {n})",
}


def _dhash(gray) -> int:
    import cv2

    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = small[:, 1:] > small[:, :-1]
    bits = 0
    for v in diff.flatten():
        bits = (bits << 1) | int(v)
    return bits


def check_images(items: List[Tuple[bytes, str]]) -> Dict[str, Any]:
    """items = [(bytes, content_type), ...] → {"ok", "problems": [{"index","code",...}], "checked", "skipped"}"""
    import cv2
    import numpy as np

    problems: List[Dict[str, Any]] = []
    hashes: List[Tuple[int, int]] = []
    skipped = 0
    for i, (data, content_type) in enumerate(items):
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            if (content_type or "").lower() in ("image/heic", "image/heif"):
                skipped += 1  # OpenCV لا يقرأ HEIC: لا نرفضها بل نتخطى فحصها
                continue
            problems.append({"index": i, "code": "unreadable"})
            continue
        h, w = img.shape[:2]
        if min(h, w) < MIN_SIDE:
            problems.append({"index": i, "code": "too_small"})
            continue
        scale = _ANALYZE_SIDE / max(h, w)
        if scale < 1:
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        mean = float(gray.mean())
        if mean < DARK_MEAN:  # السطوع أولاً: الصورة المظلمة تبدو ضبابية رقمياً
            problems.append({"index": i, "code": "dark"})
            continue
        if mean > BRIGHT_MEAN:
            problems.append({"index": i, "code": "bright"})
            continue
        if float(cv2.Laplacian(gray, cv2.CV_64F).var()) < BLUR_MIN_VARIANCE:
            problems.append({"index": i, "code": "blurry"})
            continue
        hv = _dhash(gray)
        dup_of = next((j for j, hj in hashes if bin(hv ^ hj).count("1") <= DUP_HAMMING), None)
        if dup_of is not None:
            problems.append({"index": i, "code": "duplicate", "of": dup_of})
            continue
        hashes.append((i, hv))
    return {"ok": not problems, "problems": problems, "checked": len(items) - skipped, "skipped": skipped}


def format_problems(problems: List[Dict[str, Any]]) -> str:
    lines = []
    for p in problems:
        msg = _MESSAGES.get(p["code"], p["code"])
        if p["code"] == "duplicate":
            msg = msg.format(n=p["of"] + 1)
        lines.append(f"الصورة رقم {p['index'] + 1}: {msg}")
    return "\n".join(lines)
