class OCRService:
    def __init__(self):
        self._ocr = None

    @property
    def ocr(self):
        """تحميل PaddleOCR كسول — فقط عند أول استخدام فعلي وليس عند استيراد
        الموديول. هذا يمنع تعطّل تشغيل السيرفر بالكامل لو بيئة PaddleOCR/torch
        معطوبة على الجهاز (نفس مشكلة WinError 126)."""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(
                lang="en",
                enable_mkldnn=False,
            )
        return self._ocr

    def extract_text(self, image_path: str) -> list[str]:
        results = self.ocr.predict(image_path)

        texts = []

        for result in results:
            data = result.json

            if isinstance(data, str):
                import json
                data = json.loads(data)

            data = data.get("res", data)

            for text, score in zip(
                data.get("rec_texts", []),
                data.get("rec_scores", []),
            ):
                if text and score >= 0.5:
                    texts.append(text.strip())

        return texts


ocr_service = OCRService()