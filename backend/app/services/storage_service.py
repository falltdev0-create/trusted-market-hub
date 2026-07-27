"""
app/services/storage_service.py — خدمة التخزين (MinIO/S3)
"""

from fastapi import UploadFile
from minio import Minio
from minio.error import S3Error
from app.core.config import settings
import uuid
import os


class StorageService:
    """خدمة التخزين"""
    
    def __init__(self):
        try:
            self.client = Minio(
                settings.STORAGE_ENDPOINT,
                access_key=settings.STORAGE_ACCESS_KEY,
                secret_key=settings.STORAGE_SECRET_KEY,
                secure=settings.STORAGE_SECURE,
            )
            self._ensure_buckets()
            self.use_minio = True
        except Exception as e:
            print(f"⚠️ Storage service unavailable, falling back to local storage: {e}")
            self.client = None
            self.use_minio = False
            # local storage path
            self.local_path = os.path.abspath(os.path.join(os.getcwd(), "uploads"))
            os.makedirs(self.local_path, exist_ok=True)
    
    def _ensure_buckets(self):
        """التأكد من وجود الـ buckets"""
        try:
            if not self.client:
                return
            for bucket in [settings.STORAGE_BUCKET_IMAGES, settings.STORAGE_BUCKET_DOCS]:
                if not self.client.bucket_exists(bucket):
                    self.client.make_bucket(bucket)
                    print(f"✅ Bucket created: {bucket}")
        except S3Error as e:
            print(f"⚠️ Storage bucket error: {e}")
    
    async def upload_file(
        self, 
        file: UploadFile, 
        path: str
    ) -> str:
        """رفع ملف"""
        try:
            # اقرأ محتوى الملف
            content = await file.read()

            if self.use_minio and self.client:
                # حدد الـ bucket بناء على نوع الملف
                bucket = (
                    settings.STORAGE_BUCKET_IMAGES 
                    if file.content_type.startswith("image")
                    else settings.STORAGE_BUCKET_DOCS
                )

                # اسم الملف الفريد
                file_key = f"{path}/{uuid.uuid4()}"

                # رفع الملف
                self.client.put_object(
                    bucket,
                    file_key,
                    content,
                    file.size,
                    content_type=file.content_type,
                )

                # إرجاع الـ URL
                url = f"/{bucket}/{file_key}"
                return url
            else:
                # Fallback: save locally
                ext = os.path.splitext(file.filename)[1]
                fname = f"{uuid.uuid4()}{ext}"
                subdir = os.path.join(self.local_path, path.replace('/', os.sep))
                os.makedirs(subdir, exist_ok=True)
                out_path = os.path.join(subdir, fname)
                with open(out_path, 'wb') as f:
                    f.write(content)
                return out_path
        except S3Error as e:
            raise Exception(f"Upload failed: {e}")
    
    def delete_file(self, bucket: str, file_key: str) -> bool:
        """حذف ملف"""
        try:
            if self.use_minio and self.client:
                self.client.remove_object(bucket, file_key)
            else:
                # local fallback: remove file if exists
                try:
                    os.remove(file_key)
                except Exception:
                    pass
            return True
        except S3Error as e:
            print(f"Delete failed: {e}")
            return False


_storage_service = None

def get_storage_service() -> StorageService:
    """احصل على instance من StorageService"""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service


#storage_service = get_storage_service()