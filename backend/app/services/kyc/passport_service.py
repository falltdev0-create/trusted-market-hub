# backend/app/services/kyc/passport_service.py
from app.services.kyc.ocr_service import ocr_service
from app.services.kyc.mrz_parser import (
    find_valid_mrz_line2,
    parse_passport_mrz,
    clean_mrz_line,
)


class PassportService:

    def extract_passport_data(self, image_path: str) -> dict:

        print("Starting Passport OCR...")

        # 1. OCR
        texts = ocr_service.extract_text(image_path)

        print("\nOCR text:")
        for text in texts:
            print(f"- {text}")

        # 2. Find valid MRZ line 2
        line2 = find_valid_mrz_line2(texts)

        if not line2:
            raise ValueError(
                "Could not find a valid passport MRZ"
            )

        print("\nValid MRZ line 2:")
        print(line2)

        # 3. Find MRZ line 1
        mrz_candidates = []

        for text in texts:
            cleaned = clean_mrz_line(text)

            if "<" in cleaned:
                mrz_candidates.append(cleaned)

        if not mrz_candidates:
            raise ValueError(
                "Could not find passport MRZ line 1"
            )

        print("\nMRZ candidates:")

        for candidate in mrz_candidates:
            print(candidate)

        # The line before line 2 is normally MRZ line 1.
        line1 = None

        for i, candidate in enumerate(mrz_candidates):

            if candidate == line2 and i > 0:
                line1 = mrz_candidates[i - 1]
                break

        if not line1:
            # Fallback: use the longest candidate that is not line2
            candidates_without_line2 = [
                candidate
                for candidate in mrz_candidates
                if candidate != line2
            ]

            if candidates_without_line2:
                line1 = max(
                    candidates_without_line2,
                    key=len,
                )

        if not line1:
            raise ValueError(
                "Could not determine passport MRZ line 1"
            )

        print("\nMRZ line 1:")
        print(line1)

        # 4. Parse MRZ
        passport_data = parse_passport_mrz(
            line1,
            line2,
        )

        return passport_data


passport_service = PassportService()