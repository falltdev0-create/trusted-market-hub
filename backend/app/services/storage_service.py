"""
app/services/storage_service.py — خدمة التخزين
التخزين المحلي هو الافتراضي (يعمل دائماً) مع دعم MinIO/S3 عند التفعيل.
كل الملفات المرفوعة تُحفظ فعلياً على السيرفر وتُقدَّم عبر /uploads.
"""

import io
import os
import uuid
from functools import cached_property

from app.core.config import settings


class StorageService:
    # ── Local disk helpers ────────────────────────────────────────────────────

    @property
    def local(self) -> bool:
        return (settings.STORAGE_BACKEND or "local").lower() == "local"

    def _save_local(self, content: bytes, key: str) -> str:
        path = os.path.join(settings.STORAGE_LOCAL_DIR, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/{key}"

    # ── MinIO client (only when STORAGE_BACKEND=minio) ────────────────────────

    @cached_property
    def client(self):
        from minio import Minio
        client = Minio(
            settings.STORAGE_ENDPOINT,
            access_key=settings.STORAGE_ACCESS_KEY,
            secret_key=settings.STORAGE_SECRET_KEY,
            secure=settings.STORAGE_SECURE,
        )
        for bucket in [settings.STORAGE_BUCKET_IMAGES, settings.STORAGE_BUCKET_DOCS]:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        return client

    def _put(self, bucket: str, key: str, content: bytes, content_type: str) -> str:
        if self.local:
            return self._save_local(content, key)
        try:
            self.client.put_object(
                bucket, key, io.BytesIO(content),
                length=len(content), content_type=content_type,
            )
            return f"http{'s' if settings.STORAGE_SECURE else ''}://{settings.STORAGE_ENDPOINT}/{bucket}/{key}"
        except Exception as e:  # fallback: لا نفقد الملف أبداً
            print(f"⚠️ storage fallback to local disk: {e}")
            return self._save_local(content, key)

    # ── Public API ────────────────────────────────────────────────────────────

    async def upload_image(self, content: bytes, filename: str, listing_id: str, index: int) -> str:
        ext = self._ext(filename, "jpg")
        key = f"listings/{listing_id}/images/{index:03d}_{uuid.uuid4().hex}.{ext}"
        return self._put(settings.STORAGE_BUCKET_IMAGES, key, content, f"image/{ext}")

    async def upload_document(self, content: bytes, filename: str, listing_id: str, doc_type: str) -> str:
        ext = self._ext(filename, "pdf")
        key = f"listings/{listing_id}/docs/{doc_type}_{uuid.uuid4().hex}.{ext}"
        ct  = "application/pdf" if ext == "pdf" else f"image/{ext}"
        return self._put(settings.STORAGE_BUCKET_DOCS, key, content, ct)

    async def upload_kyc_document(self, content: bytes, filename: str, user_id: str, doc_type: str) -> str:
        ext = self._ext(filename, "jpg")
        key = f"kyc/{user_id}/{doc_type}_{uuid.uuid4().hex}.{ext}"
        ct  = "application/pdf" if ext == "pdf" else f"image/{ext}"
        return self._put(settings.STORAGE_BUCKET_DOCS, key, content, ct)

    async def upload_avatar(self, content: bytes, filename: str, user_id: str) -> str:
        ext = self._ext(filename, "jpg")
        key = f"avatars/{user_id}/{uuid.uuid4().hex}.{ext}"
        return self._put(settings.STORAGE_BUCKET_IMAGES, key, content, f"image/{ext}")

    @staticmethod
    def _ext(filename: str, default: str) -> str:
        name = filename or ""
        return name.rsplit(".", 1)[-1].lower() if "." in name else default


# Singleton
storage_service = StorageService()
