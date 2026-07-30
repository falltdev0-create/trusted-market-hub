"""
Auth Routes — مسارات المصادقة
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt, JWTError
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, get_user_admin_role
from app.models.models import User, KYCStatus as VerificationStatus
from pydantic import BaseModel, EmailStr, ValidationError

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    kyc_status: str
    role: str = "user"
    admin_role: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _request_data(request: Request) -> dict:
    """Accept JSON and form submissions so Swagger/admin tools do not get 422."""
    ctype = request.headers.get("content-type", "")
    if "application/json" in ctype:
        try:
            data = await request.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    form = await request.form()
    return dict(form)


async def _token_response(user: User, db: AsyncSession) -> TokenResponse:
    tokens = create_tokens(str(user.id))
    admin_role = await get_user_admin_role(user, db)
    return TokenResponse(
        **tokens,
        user_id=str(user.id),
        full_name=user.full_name,
        kyc_status=user.kyc_status.value if user.kyc_status else "unverified",
        role="admin" if admin_role else (user.role.value if user.role else "user"),
        admin_role=admin_role,
    )


def create_token(data: dict, expire_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + expire_delta
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_tokens(user_id: str) -> dict:
    access = create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )
    refresh = create_token(
        {"sub": user_id, "type": "refresh"},
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
    )
    return {"access_token": access, "refresh_token": refresh}


async def get_current_user(token: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(request: Request, db: AsyncSession = Depends(get_db)):
    """تسجيل مستخدم جديد"""
    try:
        body = RegisterRequest.model_validate(await _request_data(request))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="البريد الإلكتروني مسجل مسبقاً")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        phone=body.phone,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        kyc_status=VerificationStatus.unverified,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return await _token_response(user, db)


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: AsyncSession = Depends(get_db)):
    """تسجيل الدخول"""
    try:
        body = LoginRequest.model_validate(await _request_data(request))
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="بيانات الدخول غير صحيحة")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="الحساب موقوف")

    return await _token_response(user, db)


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """تجديد رمز الوصول"""
    try:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload["sub"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    access = create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
    )
    return {"access_token": access, "token_type": "bearer"}
