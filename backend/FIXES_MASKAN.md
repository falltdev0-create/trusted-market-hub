# تعديلات مطلوبة لـ Maskan Backend

## 1. backend/requirements.txt
**استبدل السطر 4 والأسطر بعده:**

```txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.30
aiosqlite==1.3.1
asyncpg==0.29.0
aiomysql==0.2.0
PyMySQL==1.1.0
pydantic==2.7.0
pydantic-settings==2.3.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
httpx==0.27.0
minio==7.2.7
torch==2.3.0
torchvision==0.18.0
Pillow==10.3.0
numpy==1.26.4
pandas==2.2.2
scikit-learn==1.5.0
xgboost==2.0.3
lightgbm==4.1.0
easyocr==1.7.1
redis==5.0.4
python-dotenv==1.0.0
```

---

## 2. backend/app/core/database.py
**السطر 17-34 - استبدل كل هذا الكود:**

```python
engine_kwargs = {
    "echo": settings.DEBUG,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
    "pool_size": settings.DB_POOL_SIZE,
    "max_overflow": settings.DB_MAX_OVERFLOW,
}

if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
    })
elif settings.DATABASE_URL.startswith("mysql"):
    engine_kwargs.update({
        "connect_args": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    })

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)
```

---

## 3. backend/app/core/config.py
**السطر 45-48 - أضف هذا بعد ALLOWED_ORIGINS:**

```python
# ── CORS ──────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://moamalati.app",
    ]
```

---

## 4. backend/app/api/routes/listings.py

### 4.1 السطر 114-137 - استبدل دالة set_condition بالكامل:

```python
class SetConditionIn(BaseModel):
    grade: str  # "excellent" | "good" | "poor"
    score: float
    report: dict


@router.post("/{listing_id}/set-condition")
async def set_condition(
    listing_id: str,
    body: SetConditionIn,
    db: AsyncSession = Depends(get_db),
):
    """يُستدعى داخلياً من upload route بعد تحليل AI."""
    listing = await _get_or_404(listing_id, db)
    grade = ConditionGrade(body.grade)
    listing.condition_grade = grade
    listing.condition_score = body.score
    listing.condition_report = body.report
    listing.price_max_limit = get_price_limit(
        listing.category.value, listing.listing_type.value, body.grade
    )
    listing.status = ListingStatus.condition_assessed
    await db.commit()
    return {
        "condition_grade": grade.value,
        "condition_score": body.score,
        "price_max_limit": listing.price_max_limit,
        "currency": listing.currency,
    }
```

### 4.2 السطر 206 - ترتيب الـ routes (ضع GET /my قبل GET /):

```python
# ── Public: My Listings ────────────────────────────────────────────────

@router.get("/my")
async def get_my_listings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """إعلاناتي الخاصة بجميع الحالات"""
    rows = (await db.execute(
        select(Listing)
        .where(Listing.seller_id == current_user.id)
        .order_by(Listing.created_at.desc())
    )).scalars().all()
    return [_serialize(l) for l in rows]


# ── Public: Browse ────────────────────────────────────────────────────

@router.get("/")
async def get_listings(
    category:     Optional[ListingCategory] = None,
    listing_type: Optional[ListingType]     = None,
    condition:    Optional[ConditionGrade]  = None,
    city:         Optional[str]  = Query(None),
    q:            Optional[str]  = Query(None),
    min_price:    Optional[float] = None,
    max_price:    Optional[float] = None,
    page:         int = Query(1, ge=1),
    page_size:    int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
```

### 4.3 السطر 251+ - أضف هذا في النهاية:

```python
@router.get("/{listing_id}")
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    listing = await _get_or_404(listing_id, db)
    if listing.status != ListingStatus.published:
        raise HTTPException(404, "الإعلان غير متاح")
    listing.view_count = (listing.view_count or 0) + 1
    await db.commit()
    return _serialize(listing)
```

---

## 5. backend/app/api/routes/auth.py

### 5.1 السطر 161-177 - استبدل دالة refresh بالكامل:

```python
class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=dict)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            body.refresh_token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "refresh":
            raise HTTPException(401, "نوع الرمز خاطئ")
    except JWTError:
        raise HTTPException(401, "رمز التجديد غير صالح")

    access = _make_token(
        {"sub": payload["sub"], "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )
    return {"access_token": access, "token_type": "bearer"}
```

---

## 6. backend/app/api/routes/upload.py

### 6.1 السطر 40 - استبدل السطر:

```python
# OLD:
# result  = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))

# NEW:
try:
    listing_uuid = uuid.UUID(listing_id) if isinstance(listing_id, str) else listing_id
except ValueError:
    raise HTTPException(400, "معرّف الإعلان غير صالح")

result = await db.execute(select(Listing).where(Listing.id == listing_uuid))
```

### 6.2 السطر 62-68 - استبدل إضافة الصور:

```python
db.add(ListingImage(
    id=uuid.uuid4(),
    listing_id=listing_uuid,
    url=url,
    image_type="exterior" if i < 3 else "interior",
    order=i,
))
```

### 6.3 السطر 109 - استبدل:

```python
# OLD:
# result  = await db.execute(select(Listing).where(Listing.id == uuid.UUID(listing_id)))

# NEW:
try:
    listing_uuid = uuid.UUID(listing_id) if isinstance(listing_id, str) else listing_id
except ValueError:
    raise HTTPException(400, "معرّف الإعلان غير صالح")

result = await db.execute(select(Listing).where(Listing.id == listing_uuid))
```

---

## 7. backend/app/api/routes/admin.py

### 7.1 السطر 135-137 - استبدل:

```python
# OLD:
# listing = (await db.execute(
#     select(Listing).where(Listing.id == listing_id)
# )).scalar_one_or_none()

# NEW:
try:
    listing_uuid = uuid.UUID(listing_id) if isinstance(listing_id, str) else listing_id
except ValueError:
    raise HTTPException(400, "معرّف الإعلان غير صالح")

listing = (await db.execute(
    select(Listing).where(Listing.id == listing_uuid)
)).scalar_one_or_none()
```

### 7.2 السطر 141-143 - استبدل:

```python
verif = (await db.execute(
    select(ListingVerification).where(ListingVerification.listing_id == listing_uuid)
)).scalar_one_or_none()
```

### 7.3 السطر 191-193 - استبدل:

```python
# نفس الطريقة أعلاه
try:
    listing_uuid = uuid.UUID(body.listing_id) if isinstance(body.listing_id, str) else body.listing_id
except ValueError:
    raise HTTPException(400, "معرّف الإعلان غير صالح")

listing = (await db.execute(
    select(Listing).where(Listing.id == listing_uuid)
)).scalar_one_or_none()
```

### 7.4 السطر 230-232 - استبدل:

```python
verif = (await db.execute(
    select(ListingVerification).where(ListingVerification.listing_id == listing_uuid)
)).scalar_one_or_none()
```

---

## 8. backend/main.py

**بعد السطر 14 أضف:**

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
```

**بعد السطر 42 أضف:**

```python
# ── Error Handlers ─────────────────────────────────────────────────────────────
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )
```

---

## 9. إنشاء ملف .env جديد

**أنشئ `backend/.env`:**

```env
DEBUG=True
APP_NAME=معاملاتي
APP_VERSION=2.0.0

DATABASE_URL=mysql+aiomysql://root:@localhost:3306/maskandaba
REDIS_URL=redis://localhost:6379

JWT_SECRET_KEY=your-super-secret-key-change-in-production-12345
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=30

STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET_IMAGES=moamalati-images
STORAGE_BUCKET_DOCS=moamalati-docs
STORAGE_SECURE=False

ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://moamalati.app

CONDITION_MODEL_PATH=ai_models/condition_model/weights/model.pt
DOCUMENT_MODEL_PATH=ai_models/document_model/weights/model.pt
PRICING_MODEL_PATH=ai_models/pricing_model/weights/model.pkl
```

---

## خطوات التنفيذ:

```bash
cd backend

# 1. تحديث المكتبات
pip install -r requirements.txt --break-system-packages

# 2. إنشاء قاعدة البيانات
mysql -u root -e "CREATE DATABASE maskandaba CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. تشغيل الـ backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## مشاكل أخرى تحتاج حل:

### المشكلة: النماذج الـ AI لم تُدرّب
**الحل:** قم بتدريب النماذج باستخدام:

```bash
python ai_models/condition_model/predictor.py --dataset ./dataset --save ./ai_models/condition_model/weights/model.pt --epochs 60
python ai_models/document_model/predictor.py --dataset ./dataset --save ./ai_models/document_model/weights/model.pt --epochs 50
python ai_models/pricing_model/predictor.py --dataset ./dataset --save ./ai_models/pricing_model/weights/model.pkl
```

### الفرونتند: ربط الـ API
تأكد من أن الفرونتند يستخدم `http://localhost:8000/api/v1/` كـ base URL عند التطوير.

