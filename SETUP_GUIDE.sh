# دليل التشغيل والتدريب الكامل — معاملاتي
# من الصفر للنشر

## ─────────────────────────────────────────────
## المتطلبات الأساسية (ثبّتها أولاً)
## ─────────────────────────────────────────────

# Linux/Mac:
# - Python 3.11+
# - Docker + Docker Compose
# - Git
# - 8GB RAM كحد أدنى (16GB مُفضّل للتدريب)
# - GPU اختياري لكن يسرّع التدريب ×10

## ─────────────────────────────────────────────
## STEP 1 — استنساخ المشروع وإعداد الهيكل
## ─────────────────────────────────────────────

git clone https://github.com/falltdev0-create/trusted-market-hub.git
cd trusted-market-hub

# أنشئ الهيكل الجديد
mkdir -p backend/app/{core,models,services,api/routes}
mkdir -p ai_models/{condition_model/weights,document_model/weights,pricing_model/weights}
mkdir -p dataset/{train,val}/{excellent,good,poor}

# انسخ الملفات المُعاد كتابتها من Claude إلى مكانها
# (backend/main.py, app/core/config.py, ... إلخ)

## ─────────────────────────────────────────────
## STEP 2 — إعداد متغيرات البيئة
## ─────────────────────────────────────────────

cp backend/.env.example backend/.env
# عدّل backend/.env بقيمك الخاصة

## ─────────────────────────────────────────────
## STEP 3 — تشغيل Infrastructure (Docker)
## ─────────────────────────────────────────────

# من مجلد المشروع الجذر:
docker compose up -d postgres redis minio

# تحقق أن الخدمات تعمل:
docker compose ps

# النتيجة المتوقعة:
# postgres   running  0.0.0.0:5432->5432/tcp
# redis      running  0.0.0.0:6379->6379/tcp
# minio      running  0.0.0.0:9000->9000/tcp

## ─────────────────────────────────────────────
## STEP 4 — تشغيل Backend محلياً (للتطوير)
## ─────────────────────────────────────────────

cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# تشغيل الخادم:
uvicorn main:app --reload --port 8000

# API docs متاحة على:
# http://localhost:8000/api/docs

## ─────────────────────────────────────────────
## STEP 5 — تشغيل Frontend
## ─────────────────────────────────────────────

cd ../      # العودة لجذر المشروع
npm install
npm run dev
# يعمل على: http://localhost:5173

## ─────────────────────────────────────────────
## STEP 6 — جمع بيانات التدريب
## ─────────────────────────────────────────────

# الهدف: 500-1000 صورة لكل فئة (excellent/good/poor)
# للعقارات والسيارات منفصلين

# المصادر المجانية:

## أ) Roboflow Universe (الأسهل — مجاني)
# https://universe.roboflow.com
# ابحث عن: "house condition" أو "car damage"
# حمّل بصيغة "folder" أو "raw images"

## ب) Kaggle Datasets (مجاني — يحتاج حساب)
# pip install kaggle
# kaggle datasets download -d guslovesmath/used-car-images
# kaggle datasets download -d (ابحث عن: property condition assessment)

## ج) Google Images (طريقة يدوية سريعة)
# استخدم هذا السكريبت:

pip install icrawler

python3 << 'PYEOF'
from icrawler.builtin import GoogleImageCrawler

queries = {
    "excellent": [
        "luxury house interior clean new",
        "beautiful villa interior modern",
        "brand new apartment interior",
        "excellent condition car showroom",
        "new car interior clean",
    ],
    "good": [
        "used house interior normal condition",
        "apartment interior average condition",
        "used car good condition interior",
        "second hand car normal",
    ],
    "poor": [
        "damaged house interior deteriorated",
        "old apartment interior worn out",
        "car accident damage exterior",
        "car rust damaged old",
        "abandoned house interior",
    ],
}

for label, query_list in queries.items():
    for query in query_list:
        crawler = GoogleImageCrawler(
            storage={"root_dir": f"dataset/train/{label}"}
        )
        crawler.crawl(keyword=query, max_num=100)

print("✅ تم جمع الصور")
PYEOF

## د) Open Images Dataset (جوجل — أفضل جودة)
# pip install openimages
# python -c "
# from openimages.download import download_images
# download_images('./', ['House', 'Car'], limit=500)
# "

## هـ) بيانات سودانية محلية (الأهم)
# - صور عقارات من عقارات.net أو برقان
# - صور سيارات من هواكار أو سيارات السودان
# - يدوياً: اجمع 200-300 صورة وصنّفها

## ─────────────────────────────────────────────
## STEP 7 — تنظيف وتوزيع البيانات
## ─────────────────────────────────────────────

python3 << 'PYEOF'
import os, shutil, random
from pathlib import Path

def split_dataset(src_dir="dataset/train", val_ratio=0.2):
    """ينقل 20% من كل فئة إلى مجلد val"""
    for label in ["excellent", "good", "poor"]:
        train_path = Path(src_dir) / label
        val_path   = Path("dataset/val") / label
        val_path.mkdir(parents=True, exist_ok=True)

        images = list(train_path.glob("*.jpg")) + \
                 list(train_path.glob("*.jpeg")) + \
                 list(train_path.glob("*.png"))

        val_count = int(len(images) * val_ratio)
        val_images = random.sample(images, val_count)

        for img in val_images:
            shutil.move(str(img), str(val_path / img.name))

        print(f"{label}: {len(images)-val_count} train | {val_count} val")

split_dataset()

# إحصائيات
for split in ["train", "val"]:
    print(f"\n{split}:")
    for label in ["excellent", "good", "poor"]:
        count = len(list(Path(f"dataset/{split}/{label}").glob("*.*")))
        print(f"  {label}: {count} صورة")
PYEOF

## ─────────────────────────────────────────────
## STEP 8 — تدريب نموذج تقييم الحالة
## ─────────────────────────────────────────────

cd ai_models/condition_model
pip install torch torchvision Pillow numpy

# بدء التدريب:
python predictor.py \
    --dataset ../../dataset \
    --save ./weights/model.pt \
    --epochs 60 \
    --batch 12

# بـ GPU:
python predictor.py \
    --dataset ../../dataset \
    --save ./weights/model.pt \
    --epochs 60 \
    --batch 24 \
    --device cuda

# المدة المتوقعة:
# CPU فقط: 8-12 ساعة (60 epoch)
# GPU (RTX 3060):  45-90 دقيقة
# GPU (RTX 4090):  20-30 دقيقة

# للتدريب السريع (اختبار):
python predictor.py \
    --dataset ../../dataset \
    --save ./weights/model_test.pt \
    --epochs 5 \
    --batch 8

## ─────────────────────────────────────────────
## STEP 9 — تدريب نموذج التسعير (XGBoost)
## ─────────────────────────────────────────────

pip install xgboost scikit-learn joblib pandas

python3 << 'PYEOF'
"""
تدريب نموذج تقدير السعر
البيانات: ببساطة أنشئ CSV من إعلانات حقيقية
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import OrdinalEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
import xgboost as xgb
import joblib
import os

# ── إنشاء بيانات تدريب وهمية (استبدلها ببيانات حقيقية) ──────────────────────
np.random.seed(42)
N = 2000

cities = ["الخرطوم", "بحري", "أم درمان", "بورتسودان", "ودمدني"]
data = []

for _ in range(N):
    category     = np.random.choice(["house", "car"])
    listing_type = np.random.choice(["sale", "rent"])
    condition    = np.random.choice(["excellent", "good", "poor"], p=[0.3, 0.5, 0.2])
    city         = np.random.choice(cities)

    city_mult = {"الخرطوم":1.0, "بحري":0.95, "أم درمان":0.9,
                 "بورتسودان":0.85, "ودمدني":0.8}.get(city, 0.85)
    cond_mult = {"excellent":1.0, "good":0.65, "poor":0.35}[condition]

    if category == "house":
        size  = np.random.randint(80, 500)
        year  = np.random.randint(1990, 2024)
        km    = 0
        rooms = np.random.randint(2, 8)

        base = 2_000_000 if listing_type == "sale" else 30_000
        price = base * cond_mult * city_mult + size * (3000 if listing_type=="sale" else 40)
    else:
        size  = 0
        year  = np.random.randint(2000, 2024)
        km    = np.random.randint(5000, 300000)
        rooms = 0
        age   = 2025 - year

        base = 1_500_000 if listing_type == "sale" else 8_000
        price = base * cond_mult * city_mult
        if listing_type == "sale":
            price -= age * 50_000 + km * 0.5
            price  = max(price, 100_000)

    price += np.random.normal(0, price * 0.05)   # 5% noise

    data.append({
        "category": category, "listing_type": listing_type,
        "condition": condition, "city": city,
        "size": size, "bedrooms": rooms,
        "year": year, "km": km,
        "price": max(price, 0),
    })

df = pd.DataFrame(data)
print(f"Dataset: {len(df)} rows")
print(df.groupby(["category","listing_type","condition"])["price"].mean().apply(lambda x: f"{x:,.0f}"))

# ── Encoding ───────────────────────────────────────────────────────────────────
cat_cols = ["category", "listing_type", "condition", "city"]
num_cols = ["size", "bedrooms", "year", "km"]

encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
df[cat_cols] = encoder.fit_transform(df[cat_cols])

X = df[cat_cols + num_cols]
y = df["price"]

X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

# ── Train XGBoost ──────────────────────────────────────────────────────────────
model = xgb.XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    min_child_weight=3,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    early_stopping_rounds=30,
    eval_metric="mape",
)

model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=50)

mape = mean_absolute_percentage_error(y_val, model.predict(X_val))
print(f"\n✅ Val MAPE: {mape:.2%}")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs("ai_models/pricing_model/weights", exist_ok=True)
joblib.dump({
    "model":   model,
    "encoder": encoder,
    "features": cat_cols + num_cols,
    "val_mape": mape,
}, "ai_models/pricing_model/weights/model.pkl")

print("✅ Saved: ai_models/pricing_model/weights/model.pkl")
PYEOF

## ─────────────────────────────────────────────
## STEP 10 — اختبار النماذج قبل التشغيل
## ─────────────────────────────────────────────

python3 << 'PYEOF'
import sys
sys.path.insert(0, ".")

# اختبار نموذج الحالة
from ai_models.condition_model.predictor import ConditionPredictor
from PIL import Image
import io, numpy as np

print("🧪 اختبار نموذج الحالة...")
try:
    predictor = ConditionPredictor("ai_models/condition_model/weights/model.pt")

    # صورة اختبار عشوائية
    img = Image.fromarray(np.random.randint(100, 200, (300, 300, 3), dtype=np.uint8))
    buf = io.BytesIO(); img.save(buf, "JPEG"); img_bytes = buf.getvalue()

    result = predictor.predict([img_bytes, img_bytes, img_bytes, img_bytes, img_bytes])
    print(f"  Grade: {result['grade']} | Score: {result['score']} | Confidence: {result['confidence']:.2%}")
    print("  ✅ نموذج الحالة يعمل")
except Exception as e:
    print(f"  ❌ خطأ: {e}")

# اختبار نموذج التسعير
from ai_models.pricing_model.predictor import PricingPredictor
print("\n🧪 اختبار نموذج التسعير...")
try:
    pricing = PricingPredictor("ai_models/pricing_model/weights/model.pkl")
    result  = pricing.predict("house", "sale", "good", {"city": "الخرطوم", "size": 200, "bedrooms": 4})
    print(f"  Suggested: {result['suggested_price']:,.0f} SDG | Method: {result['method']}")
    print("  ✅ نموذج التسعير يعمل")
except Exception as e:
    print(f"  ❌ خطأ: {e}")

# اختبار Backend
import httpx
print("\n🧪 اختبار Backend...")
try:
    r = httpx.get("http://localhost:8000/health", timeout=3)
    print(f"  Status: {r.json()}")
    print("  ✅ Backend يعمل")
except Exception as e:
    print(f"  ❌ Backend غير متاح: {e}")
PYEOF

## ─────────────────────────────────────────────
## STEP 11 — تشغيل كل شيء بـ Docker (الإنتاج)
## ─────────────────────────────────────────────

# أنشئ Dockerfile للـ backend:
cat > backend/Dockerfile << 'DOCKEREOF'
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
DOCKEREOF

# شغّل كل الخدمات:
docker compose up -d

# تابع السجلات:
docker compose logs -f backend

## ─────────────────────────────────────────────
## STEP 12 — بيانات تدريب حقيقية (الخيارات)
## ─────────────────────────────────────────────

# الخيار 1: Roboflow (الأسرع - مجاني)
# اذهب لـ: https://universe.roboflow.com
# ابحث عن: "property condition" أو "vehicle damage"
# حمّل → اختر "Raw Images" → فك الضغط في dataset/

# الخيار 2: Kaggle
pip install kaggle
# ضع kaggle.json في ~/.kaggle/
kaggle datasets download -d calebrob6/meg-car-damage-dataset
# أو
kaggle datasets download -d datasets/vehicle-damage-detection

# الخيار 3: إنشاء dataset محلي بالتصنيف اليدوي
# أنشئ سكريبت تصنيف سريع:
python3 << 'LABELEOF'
"""
أداة تصنيف الصور اليدوي — تصنّف صورة في الثانية
"""
import os
from pathlib import Path

src = Path("images_unsorted")      # ضع صورك هنا
os.makedirs("dataset/train/excellent", exist_ok=True)
os.makedirs("dataset/train/good",      exist_ok=True)
os.makedirs("dataset/train/poor",      exist_ok=True)

images = list(src.glob("*.*"))
print(f"صور للتصنيف: {len(images)}")

for i, img_path in enumerate(images):
    print(f"\n[{i+1}/{len(images)}] {img_path.name}")
    print("افتح الصورة وصنّفها:")
    print("  1 = ممتازة (excellent)")
    print("  2 = جيدة   (good)")
    print("  3 = ضعيفة  (poor)")
    print("  s = تخطّي")

    import subprocess
    subprocess.Popen(["xdg-open", str(img_path)])  # Linux
    # subprocess.Popen(["open", str(img_path)])     # Mac

    choice = input("اختيارك: ").strip()
    label_map = {"1": "excellent", "2": "good", "3": "poor"}

    if choice in label_map:
        label = label_map[choice]
        import shutil
        shutil.copy(str(img_path), f"dataset/train/{label}/{img_path.name}")
        print(f"✅ → {label}")
    else:
        print("⏭ تخطّي")

print("\n✅ انتهى التصنيف")
LABELEOF

## ─────────────────────────────────────────────
## ملخص الروابط والمنافذ
## ─────────────────────────────────────────────

# Frontend:     http://localhost:5173
# Backend API:  http://localhost:8000
# API Docs:     http://localhost:8000/api/docs
# MinIO:        http://localhost:9001  (admin/minioadmin)
# PostgreSQL:   localhost:5432
# Redis:        localhost:6379
