"""
app/services/storage_service.py — خدمة التخزين
MinIO محلياً | AWS S3 في الإنتاج
"""

import io
import uuid
from functools import cached_property

from app.core.config import settings


class StorageService:

    async def upload_kyc_document(self,content: bytes,filename: str,user_id: str,doc_type: str,) -> str:

            ext = self._ext(filename, "jpg")

            key = f"kyc/{user_id}/{doc_type}_{uuid.uuid4().hex}.{ext}"

            content_type = (
                "application/pdf"
                if ext == "pdf"
                else f"image/{ext}"
            )

            self.client.put_object(
                settings.STORAGE_BUCKET_DOCS,
                key,
                io.BytesIO(content),
                length=len(content),
                content_type=content_type,
            )

            return self._url(settings.STORAGE_BUCKET_DOCS, key)

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

    async def upload_image(
        self, content: bytes, filename: str, listing_id: str, index: int
    ) -> str:
        ext = self._ext(filename, "jpg")
        key = f"listings/{listing_id}/images/{index:03d}_{uuid.uuid4().hex}.{ext}"
        self.client.put_object(
            settings.STORAGE_BUCKET_IMAGES, key,
            io.BytesIO(content), length=len(content),
            content_type=f"image/{ext}",
        )
        return self._url(settings.STORAGE_BUCKET_IMAGES, key)

    async def upload_document(
        self, content: bytes, filename: str, listing_id: str, doc_type: str
    ) -> str:
        ext = self._ext(filename, "pdf")
        key = f"listings/{listing_id}/docs/{doc_type}_{uuid.uuid4().hex}.{ext}"
        ct  = "application/pdf" if ext == "pdf" else f"image/{ext}"
        self.client.put_object(
            settings.STORAGE_BUCKET_DOCS, key,
            io.BytesIO(content), length=len(content), content_type=ct,
        )
        return self._url(settings.STORAGE_BUCKET_DOCS, key)

    @staticmethod
    def _ext(filename: str, default: str) -> str:
        return filename.rsplit(".", 1)[-1].lower() if "." in filename else default

    @staticmethod
    def _url(bucket: str, key: str) -> str:
        return f"http://{settings.STORAGE_ENDPOINT}/{bucket}/{key}"
    
    


# Singleton
storage_service = StorageService()
