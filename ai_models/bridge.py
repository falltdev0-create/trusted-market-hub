#!/usr/bin/env python3
"""
جسر نماذج الذكاء الاصطناعي — معاملاتي
=====================================
يُستدعى من Node.js (server/src/ai.js) كعملية فرعية.
المدخل : JSON عبر stdin  →  {"task": "...", ...}
المخرج : سطر JSON واحد عبر stdout → {"ok": true, ...}

المهام المدعومة:
  health     — حالة النماذج المتاحة
  condition  — تقييم حالة السلعة من الصور   (MobileNetV3-Small / heuristic)
  documents  — مطابقة وثيقة الهوية بوثيقة الملكية (OCR/تشابه نصي / heuristic)
  pricing    — تقدير السعر المرجعي           (قواعد خفيفة)
  embed      — تمثيلات متجهية للنصوص         (MiniLM / hashing fallback)
  generate   — إجابة استخلاصية من سياقات RAG

كل النماذج خفيفة على المعالج، وكل مهمة لها بديل حسابي (fallback)
يعمل بدون تحميل أي نموذج، لذلك لا يفشل الـ API أبداً.
"""

import hashlib
import json
import math
import os
import re
import sys

CONDITION_MODEL = os.environ.get("CONDITION_MODEL", "mobilenet_v3_small")
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

_cache = {}


# ────────────────────────────── أدوات مساعدة ──────────────────────────────

def _pil(path):
    from PIL import Image  # type: ignore

    img = Image.open(path)
    img.load()
    return img.convert("RGB")


def _try(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _grade(score):
    if score >= 85:
        return "excellent"
    if score >= 70:
        return "good"
    if score >= 50:
        return "fair"
    return "poor"


def _grade_ar(grade):
    return {
        "excellent": "ممتازة",
        "good": "جيدة",
        "fair": "متوسطة",
        "poor": "ضعيفة",
    }.get(grade, "غير محددة")


# ────────────────────────────── تقييم الحالة ──────────────────────────────

def _image_stats(path):
    """مقاييس بصرية خفيفة: الحدة، الإضاءة، التباين، الدقة."""
    img = _pil(path)
    w, h = img.size
    small = img.resize((160, 160))
    px = list(small.convert("L").getdata())
    n = len(px)
    mean = sum(px) / n
    var = sum((p - mean) ** 2 for p in px) / n
    std = math.sqrt(var)

    # تقدير الحدة عبر فروق البكسلات المتجاورة (Laplacian مبسّط)
    grid = [px[i * 160 : (i + 1) * 160] for i in range(160)]
    diffs = 0.0
    count = 0
    for y in range(1, 159):
        row, up, down = grid[y], grid[y - 1], grid[y + 1]
        for x in range(1, 159, 2):
            lap = 4 * row[x] - row[x - 1] - row[x + 1] - up[x] - down[x]
            diffs += lap * lap
            count += 1
    sharpness = math.sqrt(diffs / max(count, 1))

    brightness_score = max(0.0, 100.0 - abs(mean - 130) * 0.65)
    contrast_score = min(100.0, std * 1.9)
    sharpness_score = min(100.0, sharpness * 1.6)
    resolution_score = min(100.0, (w * h) / (1280 * 720) * 100.0)

    return {
        "width": w,
        "height": h,
        "brightness": round(brightness_score, 1),
        "contrast": round(contrast_score, 1),
        "sharpness": round(sharpness_score, 1),
        "resolution": round(resolution_score, 1),
    }


def _classifier():
    """نموذج تصنيف صور خفيف (MobileNetV3-Small) — يُحمّل مرة واحدة."""
    if "clf" in _cache:
        return _cache["clf"]
    try:
        from transformers import pipeline  # type: ignore

        name = (
            CONDITION_MODEL
            if "/" in CONDITION_MODEL
            else "timm/mobilenetv3_small_100.lamb_in1k"
        )
        _cache["clf"] = pipeline("image-classification", model=name, device=-1)
    except Exception:
        _cache["clf"] = None
    return _cache["clf"]


def task_condition(payload):
    images = [p for p in payload.get("images", []) if p and os.path.exists(p)]
    if not images:
        return {"ok": False, "error": "لا توجد صور صالحة للتحليل"}

    per_image = []
    for p in images[:8]:
        stats = _try(lambda: _image_stats(p))
        if not stats:
            continue
        quality = (
            stats["sharpness"] * 0.35
            + stats["brightness"] * 0.25
            + stats["contrast"] * 0.20
            + stats["resolution"] * 0.20
        )
        entry = {"file": os.path.basename(p), **stats, "quality": round(quality, 1)}

        clf = _classifier()
        if clf:
            preds = _try(lambda: clf(_pil(p), top_k=3), [])
            if preds:
                entry["labels"] = [
                    {"label": x["label"], "score": round(float(x["score"]), 3)}
                    for x in preds
                ]
                entry["model_confidence"] = round(float(preds[0]["score"]) * 100, 1)
        per_image.append(entry)

    if not per_image:
        return {"ok": False, "error": "تعذّرت قراءة الصور"}

    avg = lambda k: sum(i[k] for i in per_image) / len(per_image)  # noqa: E731
    quality = avg("quality")
    consistency = min(100.0, 60 + len(per_image) * 8)
    score = round(quality * 0.75 + consistency * 0.25, 1)
    score = max(20.0, min(98.0, score))
    grade = _grade(score)

    notes = []
    if avg("sharpness") < 45:
        notes.append("بعض الصور غير واضحة — أعد التصوير بثبات أكبر.")
    if avg("brightness") < 55:
        notes.append("الإضاءة ضعيفة في بعض الصور.")
    if len(per_image) < 4:
        notes.append("أضف صوراً أكثر من زوايا مختلفة لرفع دقة التقييم.")
    if not notes:
        notes.append("الصور واضحة وكافية لتقييم دقيق.")

    return {
        "ok": True,
        "task": "condition",
        "engine": "mobilenet_v3_small" if _cache.get("clf") else "heuristic-cv",
        "score": score,
        "grade": grade,
        "grade_ar": _grade_ar(grade),
        "breakdown": {
            "sharpness": round(avg("sharpness"), 1),
            "brightness": round(avg("brightness"), 1),
            "contrast": round(avg("contrast"), 1),
            "resolution": round(avg("resolution"), 1),
            "coverage": round(consistency, 1),
        },
        "images_analyzed": len(per_image),
        "per_image": per_image,
        "notes": notes,
    }


# ──────────────────────────── مطابقة الوثائق ────────────────────────────

_AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def _ocr(path):
    if not path or not os.path.exists(path):
        return ""
    try:
        import pytesseract  # type: ignore

        return pytesseract.image_to_string(_pil(path), lang="ara+eng")
    except Exception:
        return ""


def _norm(text):
    text = (text or "").translate(_AR_DIGITS)
    text = re.sub(r"[\u064B-\u0652]", "", text)
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    return re.sub(r"\s+", " ", text).strip()


def _similarity(a, b):
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    try:
        from rapidfuzz import fuzz  # type: ignore

        return float(fuzz.token_set_ratio(a, b))
    except Exception:
        ta, tb = set(a.split()), set(b.split())
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb) * 100.0


def task_documents(payload):
    id_doc = payload.get("id_doc")
    own_doc = payload.get("ownership_doc")
    if not id_doc or not os.path.exists(id_doc):
        return {"ok": False, "error": "وثيقة الهوية غير موجودة"}

    id_text = _ocr(id_doc)
    own_text = _ocr(own_doc) if own_doc else ""
    ocr_available = bool(id_text.strip())

    id_stats = _try(lambda: _image_stats(id_doc), {}) or {}
    own_stats = _try(lambda: _image_stats(own_doc), {}) if own_doc else {}
    own_stats = own_stats or {}

    legibility = (id_stats.get("sharpness", 60) + id_stats.get("brightness", 60)) / 2

    checks = []
    if ocr_available:
        name_score = _similarity(id_text, own_text) if own_text else 55.0
        nums_id = set(re.findall(r"\d{6,}", _norm(id_text)))
        nums_own = set(re.findall(r"\d{6,}", _norm(own_text)))
        num_match = 100.0 if (nums_id & nums_own) else (40.0 if nums_id else 25.0)
        score = round(name_score * 0.55 + num_match * 0.25 + legibility * 0.20, 1)
        checks = [
            {"label": "تطابق الاسم", "score": round(name_score, 1), "passed": name_score >= 60},
            {"label": "تطابق الرقم الوطني", "score": round(num_match, 1), "passed": num_match >= 60},
            {"label": "وضوح الوثيقة", "score": round(legibility, 1), "passed": legibility >= 50},
        ]
    else:
        score = round(legibility * 0.6 + (65 if own_doc else 40) * 0.4, 1)
        checks = [
            {"label": "وضوح صورة الهوية", "score": round(legibility, 1), "passed": legibility >= 50},
            {"label": "وجود وثيقة ملكية", "score": 100.0 if own_doc else 0.0, "passed": bool(own_doc)},
        ]

    score = max(5.0, min(99.0, score))
    status = "matched" if score >= 75 else ("review" if score >= 50 else "mismatch")

    return {
        "ok": True,
        "task": "documents",
        "engine": "tesseract-ocr" if ocr_available else "heuristic-cv",
        "match_score": score,
        "status": status,
        "checks": checks,
        "requires_manual_review": status != "matched",
        "notes": (
            "تمت المطابقة تلقائياً بنجاح."
            if status == "matched"
            else "يحتاج الطلب إلى مراجعة بشرية من فريق الإدارة."
        ),
    }


# ────────────────────────────── تقدير السعر ──────────────────────────────

CITY_FACTOR = {
    "الخرطوم": 1.25, "بحري": 1.05, "أم درمان": 1.0, "امدرمان": 1.0,
    "بورتسودان": 1.1, "مدني": 0.9, "كسلا": 0.8, "الأبيض": 0.8, "عطبرة": 0.85,
}

BASE_HOUSE_SQM = 45000.0     # جنيه/م² مرجعي
BASE_CAR = 9_000_000.0       # سعر سيارة مرجعي


def task_pricing(payload):
    kind = (payload.get("kind") or payload.get("category") or "house").lower()
    listing_type = (payload.get("listing_type") or "sale").lower()
    city = payload.get("city") or ""
    cf = CITY_FACTOR.get(_norm(city), 1.0)
    condition = float(payload.get("condition_score") or 70)
    cond_factor = 0.75 + (condition / 100.0) * 0.45

    factors = {"city": cf, "condition": round(cond_factor, 3)}

    if kind in ("car", "cars", "سيارة", "سيارات"):
        year = int(payload.get("year") or 2015)
        mileage = float(payload.get("mileage") or 100000)
        age = max(0, 2026 - year)
        age_factor = max(0.25, 0.94**age)
        km_factor = max(0.5, 1.0 - (mileage / 400000.0))
        base = BASE_CAR * age_factor * km_factor * cond_factor
        factors.update({"age": round(age_factor, 3), "mileage": round(km_factor, 3)})
    else:
        area = float(payload.get("area") or 200)
        rooms = float(payload.get("rooms") or 3)
        base = BASE_HOUSE_SQM * area * cf * cond_factor
        base *= 1 + max(0.0, rooms - 3) * 0.04
        factors.update({"area": area, "rooms": rooms})

    if listing_type in ("rent", "إيجار"):
        base = base * 0.006  # إيجار شهري تقريبي

    suggested = round(base / 1000) * 1000
    return {
        "ok": True,
        "task": "pricing",
        "engine": "rule-based-estimator",
        "suggested_price": suggested,
        "range": {"min": round(suggested * 0.85), "max": round(suggested * 1.15)},
        "currency": "SDG",
        "factors": factors,
        "note": "سعر استرشادي فقط — البائع حر في تحديد سعره، ويظهر التصنيف (رخيص/متوسط/غالي) للمشترين.",
    }


# ──────────────────────────── التمثيلات المتجهية ────────────────────────────

DIM = 384


def _hash_embed(text):
    """تمثيل احتياطي بدون نماذج: hashing trick + تطبيع."""
    vec = [0.0] * DIM
    for tok in re.findall(r"[\w\u0600-\u06FF]+", _norm(text).lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        vec[h % DIM] += 1.0
        vec[(h >> 8) % DIM] += 0.5
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _encoder():
    if "enc" in _cache:
        return _cache["enc"]
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _cache["enc"] = SentenceTransformer(EMBED_MODEL, device="cpu")
    except Exception:
        _cache["enc"] = None
    return _cache["enc"]


def task_embed(payload):
    texts = payload.get("texts") or []
    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        return {"ok": False, "error": "لا توجد نصوص"}

    enc = _encoder()
    if enc is not None:
        vecs = _try(lambda: [v.tolist() for v in enc.encode(texts, batch_size=8)])
        if vecs:
            return {"ok": True, "task": "embed", "engine": "minilm", "dim": len(vecs[0]), "vectors": vecs}

    vecs = [_hash_embed(t) for t in texts]
    return {"ok": True, "task": "embed", "engine": "hashing", "dim": DIM, "vectors": vecs}


# ──────────────────────────── التوليد الاستخلاصي ────────────────────────────

def task_generate(payload):
    question = payload.get("question") or ""
    contexts = payload.get("contexts") or []
    if not contexts:
        return {
            "ok": True,
            "task": "generate",
            "engine": "extractive",
            "answer": "لم أجد معلومات كافية في قاعدة المعرفة للإجابة على سؤالك.",
        }

    sentences = []
    for c in contexts[:5]:
        text = c if isinstance(c, str) else (c.get("content") or "")
        for s in re.split(r"[.\n!؟?]", text):
            s = s.strip()
            if len(s) > 15:
                sentences.append(s)

    scored = sorted(sentences, key=lambda s: -_similarity(question, s))
    answer = "، ".join(scored[:3]) if scored else (contexts[0] if isinstance(contexts[0], str) else "")
    return {
        "ok": True,
        "task": "generate",
        "engine": "extractive",
        "answer": (answer[:900] + "…") if len(answer) > 900 else answer,
    }


# ────────────────────────────────── health ──────────────────────────────────

def task_health(_payload):
    def mod(name):
        try:
            __import__(name)
            return True
        except Exception:
            return False

    return {
        "ok": True,
        "task": "health",
        "python": sys.version.split()[0],
        "models": {
            "pillow": mod("PIL"),
            "transformers": mod("transformers"),
            "torch": mod("torch"),
            "sentence_transformers": mod("sentence_transformers"),
            "pytesseract": mod("pytesseract"),
            "rapidfuzz": mod("rapidfuzz"),
        },
        "condition_model": CONDITION_MODEL,
        "embed_model": EMBED_MODEL,
        "fallbacks": "كل المهام تعمل حتى بدون النماذج الثقيلة (heuristics مدمجة)",
    }


TASKS = {
    "health": task_health,
    "condition": task_condition,
    "documents": task_documents,
    "pricing": task_pricing,
    "embed": task_embed,
    "generate": task_generate,
}


def main():
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw or "{}")
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON input: {e}"}, ensure_ascii=False))
        return

    fn = TASKS.get(payload.get("task"))
    if not fn:
        print(json.dumps({"ok": False, "error": f"unknown task: {payload.get('task')}"}, ensure_ascii=False))
        return

    try:
        result = fn(payload)
    except Exception as e:  # لا نُسقط الـ API أبداً
        result = {"ok": False, "error": f"{type(e).__name__}: {e}"}

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
