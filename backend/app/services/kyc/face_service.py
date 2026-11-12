"""
مطابقة وجه الهوية مع السيلفي — OpenCV YuNet (كشف) + SFace (تمثيل) عبر ONNX على CPU.

الملفات المطلوبة (حوالي 40MB معاً) في backend/models/face/ :
  face_detection_yunet_2023mar.onnx
  face_recognition_sface_2021dec.onnx

النتيجة استرشادية للمشرف وليست قبولاً نهائياً.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Any

log = logging.getLogger(__name__)

MODEL_DIR = os.environ.get(
    "FACE_MODEL_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "face"),
)
DETECTOR_FILE = "face_detection_yunet_2023mar.onnx"
RECOGNIZER_FILE = "face_recognition_sface_2021dec.onnx"

# العتبة الموصى بها من OpenCV لقرار "نفس الشخص" بمقياس cosine. عايرها على بياناتكم.
COSINE_THRESHOLD = 0.363
MAX_SIDE = 1280


class FaceService:
    def __init__(self) -> None:
        self._detector = None
        self._recognizer = None
        self._lock = threading.Lock()

    # ── lazy load ────────────────────────────────────────────────────────
    def _load(self) -> None:
        if self._detector is not None and self._recognizer is not None:
            return
        import cv2

        det_path = os.path.abspath(os.path.join(MODEL_DIR, DETECTOR_FILE))
        rec_path = os.path.abspath(os.path.join(MODEL_DIR, RECOGNIZER_FILE))
        for p in (det_path, rec_path):
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Face model missing: {p}")
        self._detector = cv2.FaceDetectorYN.create(
            det_path, "", (320, 320), score_threshold=0.8, nms_threshold=0.3, top_k=50
        )
        self._recognizer = cv2.FaceRecognizerSF.create(rec_path, "")

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _decode(data: bytes):
        import cv2
        import numpy as np

        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return None
        h, w = img.shape[:2]
        scale = MAX_SIDE / max(h, w)
        if scale < 1:
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        return img

    def _largest_face_feature(self, img):
        h, w = img.shape[:2]
        self._detector.setInputSize((w, h))
        _, faces = self._detector.detect(img)
        if faces is None or len(faces) == 0:
            return None, 0
        # أكبر وجه (صورة الهوية قد تحتوي صورة شبحية صغيرة)
        face = max(faces, key=lambda f: float(f[2]) * float(f[3]))
        aligned = self._recognizer.alignCrop(img, face)
        return self._recognizer.feature(aligned), int(len(faces))

    # ── public ───────────────────────────────────────────────────────────
    def compare(self, id_bytes: bytes, selfie_bytes: bytes) -> dict[str, Any]:
        """يرجع دائماً قاموساً ولا يرفع استثناء: verdict ∈ match | no_match | no_face | error."""
        try:
            import cv2

            with self._lock:  # الكائنات غير آمنة للتوازي
                self._load()
                id_img = self._decode(id_bytes)
                selfie_img = self._decode(selfie_bytes)
                if id_img is None or selfie_img is None:
                    return {"verdict": "error", "score": None, "reason": "unreadable_image"}

                id_feat, id_faces = self._largest_face_feature(id_img)
                selfie_feat, selfie_faces = self._largest_face_feature(selfie_img)
                if id_feat is None or selfie_feat is None:
                    return {
                        "verdict": "no_face",
                        "score": None,
                        "id_face_found": id_feat is not None,
                        "selfie_face_found": selfie_feat is not None,
                    }

                score = float(
                    self._recognizer.match(id_feat, selfie_feat, cv2.FaceRecognizerSF_FR_COSINE)
                )
            return {
                "verdict": "match" if score >= COSINE_THRESHOLD else "no_match",
                "score": round(score, 4),
                "threshold": COSINE_THRESHOLD,
                "selfie_faces": selfie_faces,
                "id_faces": id_faces,
                "model": "yunet+sface",
            }
        except FileNotFoundError as exc:
            log.warning("%s", exc)
            return {"verdict": "error", "score": None, "reason": "model_missing"}
        except Exception:
            log.exception("Face comparison failed")
            return {"verdict": "error", "score": None, "reason": "internal_error"}


face_service = FaceService()