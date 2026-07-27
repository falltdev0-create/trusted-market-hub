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