import cv2
from paddleocr import PaddleOCR


class MRZOCRService:
    def __init__(self):
        self.ocr = PaddleOCR(
            lang="en",
            enable_mkldnn=False,
        )

    def extract_mrz(self, image_path: str):
        image = cv2.imread(image_path)

        if image is None:
            raise ValueError(f"Could not read image: {image_path}")

        height, width = image.shape[:2]

        # MRZ is normally located at the bottom of the passport.
        crop = image[int(height * 0.70):height, :]

        result = self.ocr.predict(crop)

        texts = []

        for page in result:
            data = page.json

            if isinstance(data, str):
                import json
                data = json.loads(data)

            data = data.get("res", data)

            texts.extend(data.get("rec_texts", []))

        return texts


mrz_ocr_service = MRZOCRService()