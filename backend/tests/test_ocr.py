from app.services.kyc.ocr_service import ocr_service


image_path = "test_images/id_card.jpg"

print("Starting OCR...")

texts = ocr_service.extract_text(image_path)

print("\nDetected text:")

for i, text in enumerate(texts):
    print(f"{i}: {repr(text)}")