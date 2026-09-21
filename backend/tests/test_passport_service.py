from app.services.kyc.passport_service import passport_service


IMAGE_PATH = "test_images/id_card.jpg"


def main():
    print("Starting Passport Service test...")

    try:
        result = passport_service.extract_passport_data(
            IMAGE_PATH
        )

        print("\nPassport Service result:")

        for key, value in result.items():
            print(f"{key}: {value}")

    except Exception as e:
        print("\nERROR:")
        print(type(e).__name__)
        print(e)


if __name__ == "__main__":
    main()