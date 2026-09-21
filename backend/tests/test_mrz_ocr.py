from app.services.kyc.mrz_ocr_service import mrz_ocr_service


print("Starting MRZ OCR...")

texts = mrz_ocr_service.extract_mrz(
    "test_images/id_card.jpg"
)

print("\nMRZ OCR result:")

for text in texts:
    print("-", text)