"""
app/core/security.py — Security utilities for the Maskan application
This module provides functions and dependencies for:
JWT Token Management, Password Hashing, Role-Based Access Control
"""

from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db
from app.models.models import User, UserRole

# ── Password Context ──────────────────────────────────────────────────────────
# dynamically choose the best hashing algorithm available
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Security Scheme ───────────────────────────────────────────────────────────
# Bearer token authentication
http_bearer = HTTPBearer()


# ═══════════════════════════════════════════════════════════════════════════════
# PASSWORD MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: string password to hash
    
    Returns:
        hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    التحقق من كلمة المرور
    
    Args:
        plain_password: كلمة المرور النصية
        hashed_password: كلمة المرور المشفرة المخزنة
    
    Returns:
        True إذا كانت كلمة المرور صحيحة
    """
    return pwd_context.verify(plain_password, hashed_password)


# ═══════════════════════════════════════════════════════════════════════════════
# JWT TOKEN MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """
    إنشاء رمز الوصول (Access Token)
    
    Args:
        user_id: معرّف المستخدم
        expires_delta: مدة صلاحية الرمز (اختياري، الافتراضي 60 دقيقة)
    
    Returns:
        JWT token مشفر
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": user_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    إنشاء رمز التجديد (Refresh Token)
    
    Args:
        user_id: معرّف المستخدم
    
    Returns:
        JWT token مشفر للتجديد
    """
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow()
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    التحقق من صحة الرمز وفك تشفيره
    
    Args:
        token: JWT token للتحقق منه
    
    Returns:
        قاموس يحتوي على user_id, token_type, والـ payload الكامل
    
    Raises:
        HTTPException: إذا كان الرمز غير صالح أو منتهي الصلاحية
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="رمز غير صالح: بيانات مفقودة",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"user_id": user_id, "token_type": token_type, "payload": payload}
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز غير صالح أو منتهي الصلاحية",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DEPENDENCIES - AUTHENTICATION & AUTHORIZATION
# ═══════════════════════════════════════════════════════════════════════════════

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    الحصول على المستخدم الحالي من الـ token
    
    يتم استخدام هذا الـ dependency في جميع الـ endpoints التي تتطلب مصادقة
    
    Args:
        credentials: بيانات المصادقة من Bearer token
        db: جلسة قاعدة البيانات
    
    Returns:
        كائن المستخدم من قاعدة البيانات
    
    Raises:
        HTTPException: إذا كان الرمز غير صالح أو المستخدم معطل
    """
    token = credentials.credentials
    decoded = verify_token(token)
    user_id = decoded["user_id"]
    
    # البحث عن المستخدم في قاعدة البيانات
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="المستخدم غير موجود أو موقوف"
        )
    
    return user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    التحقق من أن المستخدم الحالي مشرف أو مدير
    
    يتم استخدام هذا الـ dependency في endpoints الإدارة فقط
    
    Args:
        current_user: المستخدم الحالي
    
    Returns:
        المستخدم إذا كان مشرفاً
    
    Raises:
        HTTPException: إذا كان المستخدم ليس مشرفاً
    """
    if current_user.role not in (UserRole.admin, UserRole.manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات المشرف مطلوبة"
        )
    return current_user


async def require_seller(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    التحقق من أن المستخدم الحالي بائع
    
    يتم استخدام هذا الـ dependency في endpoints البيع
    
    Args:
        current_user: المستخدم الحالي
    
    Returns:
        المستخدم إذا كان بائعاً
    
    Raises:
        HTTPException: إذا كان المستخدم ليس بائعاً
    """
    if current_user.role not in (UserRole.seller, UserRole.both):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات البائع مطلوبة"
        )
    return current_user


async def require_buyer(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    التحقق من أن المستخدم الحالي مشتري
    
    يتم استخدام هذا الـ dependency في endpoints الشراء
    
    Args:
        current_user: المستخدم الحالي
    
    Returns:
        المستخدم إذا كان مشترياً
    
    Raises:
        HTTPException: إذا كان المستخدم ليس مشترياً
    """
    if current_user.role not in (UserRole.buyer, UserRole.both):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="صلاحيات المشتري مطلوبة"
        )
    return current_user


async def get_current_admin(
    admin: User = Depends(require_admin)
) -> User:
    """
    سهلة الاستخدام: الحصول على المستخدم الإداري المصرح
    """
    return admin
