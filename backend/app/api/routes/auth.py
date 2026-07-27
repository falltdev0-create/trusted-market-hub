<<<<<<< HEAD
"""auth routes — مسارات المصادقة (mini)
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User

router = APIRouter()


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    """تحديث التوكن"""
    from app.core.security import verify_refresh_token, create_tokens
    
    try:
        user_id = verify_refresh_token(refresh_token)
    except:
        raise HTTPException(401, "توكن منتهي الصلاحية")
    
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(401, "المستخدم غير موجود")
    
    access_token, refresh_token = create_tokens(str(user.id))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
):
    """تسجيل الخروج"""
    # يمكن إضافة blacklist للـ tokens هنا
    return {"message": "تم تسجيل الخروج بنجاح"}


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """التحقق من البريد الإلكتروني"""
    try:
        # فك تشفير التوكن واحصل على البريد
        # هذا مثال مبسط - يجب تحسينه
        email = token  # في الواقع، استخرج البريد من التوكن
        
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if user:
            user.is_verified = True
            await db.commit()
            return {"message": "تم التحقق من البريد بنجاح"}
    except Exception as e:
        raise HTTPException(400, f"التحقق فشل: {e}")
=======
"""
app/api/routes/auth.py — مسارات المصادقة
تسجيل | دخول | تجديد الرمز
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.models import User, KYCStatus

router = APIRouter()
pwd    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterIn(BaseModel):
    full_name: str
    email:     EmailStr
    phone:     str
    password:  str


class LoginIn(BaseModel):
    email:    EmailStr
    password: str


class TokenOut(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    user_id:       str
    full_name:     str
    kyc_status:    str


# ── Token helpers ─────────────────────────────────────────────────────────────

def _make_token(data: dict, delta: timedelta) -> str:
    return jwt.encode(
        {**data, "exp": datetime.utcnow() + delta},
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _token_pair(user_id: str) -> dict:
    return {
        "access_token":  _make_token(
            {"sub": user_id, "type": "access"},
            timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        ),
        "refresh_token": _make_token(
            {"sub": user_id, "type": "refresh"},
            timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        ),
    }


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_current_user(
    token: str = Depends(oauth2),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(401, "رمز الوصول غير صالح")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user   = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "المستخدم غير موجود أو موقوف")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenOut, status_code=201)
async def register(body: RegisterIn, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(User).where(User.email == body.email))).scalar_one_or_none():
        raise HTTPException(409, "البريد الإلكتروني مسجل مسبقاً")

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        phone=body.phone,
        password_hash=pwd.hash(body.password),
        full_name=body.full_name,
        kyc_status=KYCStatus.pending,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return TokenOut(
        **_token_pair(str(user.id)),
        user_id=str(user.id),
        full_name=user.full_name,
        kyc_status=user.kyc_status.value,
    )


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user   = result.scalar_one_or_none()

    if not user or not pwd.verify(body.password, user.password_hash):
        raise HTTPException(401, "بيانات الدخول غير صحيحة")
    if not user.is_active:
        raise HTTPException(403, "الحساب موقوف")

    return TokenOut(
        **_token_pair(str(user.id)),
        user_id=str(user.id),
        full_name=user.full_name,
        kyc_status=user.kyc_status.value,
    )


@router.post("/refresh")
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(
            refresh_token, settings.JWT_SECRET_KEY,
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
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b
