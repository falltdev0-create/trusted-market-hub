"""
app/core/dynamic_settings.py — قراءة إعدادات قابلة للتغيير من لوحة الإدارة
(جدول system_settings) بدل قيم ثابتة في config.py، مع كاش قصير العمر (15
ثانية) عشان ما نضرب قاعدة البيانات في كل طلب.

تُكتب هذه الإعدادات عبر المسارات العامة الموجودة أصلاً:
  GET /admin/settings          — عرض كل الإعدادات
  PUT /admin/settings/{key}    — تعديل إعداد واحد  (body: {"value": ...})
"""
import time
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CACHE: dict[str, tuple[float, Any]] = {}
_TTL_SECONDS = 15


async def get_dynamic_setting(db: AsyncSession, key: str, default: Any) -> Any:
    now = time.time()
    cached = _CACHE.get(key)
    if cached and now - cached[0] < _TTL_SECONDS:
        return cached[1]

    value = default
    try:
        row = (await db.execute(
            text("SELECT setting_value FROM system_settings WHERE setting_key = :k"),
            {"k": key},
        )).first()
        if row is not None:
            value = row[0]
    except Exception:
        pass

    _CACHE[key] = (now, value)
    return value


def invalidate_cache(key: str | None = None) -> None:
    """يُستدعى بعد تعديل إعداد من لوحة الإدارة عشان القيمة الجديدة تنعكس فوراً
    بدل ما ننتظر انتهاء الكاش (حتى 15 ثانية)."""
    if key is None:
        _CACHE.clear()
    else:
        _CACHE.pop(key, None)
