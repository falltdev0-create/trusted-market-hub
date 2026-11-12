import re


MRZ_WEIGHTS = [7, 3, 1]


def mrz_char_value(char: str) -> int:
    if char == "<":
        return 0

    if char.isdigit():
        return int(char)

    return ord(char) - ord("A") + 10


def calculate_check_digit(value: str) -> str:
    total = 0

    for i, char in enumerate(value):
        total += mrz_char_value(char) * MRZ_WEIGHTS[i % 3]

    return str(total % 10)


def validate_check_digit(value: str, check_digit: str) -> bool:
    if not check_digit.isdigit():
        return False

    return calculate_check_digit(value) == check_digit


def clean_mrz_line(line: str) -> str:
    line = line.upper().replace(" ", "")
    return re.sub(r"[^A-Z0-9<]", "", line)


def find_mrz_lines(texts: list[str]) -> list[str]:
    candidates = []

    for text in texts:
        cleaned = clean_mrz_line(text)

        if "<" in cleaned and len(cleaned) >= 20:
            candidates.append(cleaned)

    return candidates


def find_valid_mrz_line2(texts: list[str]) -> str | None:
    for text in texts:
        line = clean_mrz_line(text)

        if len(line) < 28:
            continue

        # OCR may miss the leading "P" in passport MRZ.
        # Try the original line first.
        candidates = [line]

        # If the line starts with 9 digits followed by
        # the nationality code, try adding "P".
        if (
            len(line) >= 12
            and line[:9].isdigit()
            and line[9:12].isalpha()
        ):
            candidates.append("P" + line)

        for candidate in candidates:

            if len(candidate) < 28:
                continue

            passport_number = candidate[0:9]
            passport_check_digit = candidate[9]

            birth_date = candidate[13:19]
            birth_check_digit = candidate[19]

            expiry_date = candidate[21:27]
            expiry_check_digit = candidate[27]

            passport_valid = validate_check_digit(
                passport_number,
                passport_check_digit,
            )

            birth_valid = validate_check_digit(
                birth_date,
                birth_check_digit,
            )

            expiry_valid = validate_check_digit(
                expiry_date,
                expiry_check_digit,
            )

            if (
                passport_valid
                and birth_valid
                and expiry_valid
            ):
                return candidate

    return None


def parse_passport_mrz(line1: str, line2: str) -> dict:
    line1 = clean_mrz_line(line1)
    line2 = clean_mrz_line(line2)

    if len(line2) < 28:
        raise ValueError("Invalid MRZ line 2")

    # ---------------------------------------------------------
    # Line 2
    # ---------------------------------------------------------

    passport_number = line2[0:9].replace("<", "")

    nationality = line2[10:13].replace("<", "")

    birth_date_raw = line2[13:19]

    sex = line2[20:21]

    expiry_date_raw = line2[21:27]

        # ---------------------------------------------------------
    # Line 1
    # ---------------------------------------------------------

    # OCR result for this passport:
    #
    # CSDNMOHAMED<ABDALLA<ABDELAAL<MOHAMED<<
    #
    # Expected meaning:
    # PC  -> document type
    # SDN -> country
    #
    # OCR dropped the "P" and merged the document type
    # with the country code.

    if line1.startswith("CSDN"):
        document_type = "PC"
        country = "SDN"
        name_section = line1[4:]

    elif line1.startswith("PC"):
        document_type = "PC"
        country = nationality
        name_section = line1[2:]

        if name_section.startswith(country):
            name_section = name_section[3:]

    elif line1.startswith("P<"):
        document_type = "P"
        country = nationality
        name_section = line1[2:]

        if name_section.startswith(country):
            name_section = name_section[3:]

    elif line1.startswith("P"):
        document_type = "P"
        country = nationality
        name_section = line1[1:]

        if name_section.startswith(country):
            name_section = name_section[3:]

    else:
        document_type = line1[:2]
        country = nationality
        name_section = line1[2:]

        if name_section.startswith(country):
            name_section = name_section[3:]

    # Remove separators
    name_section = name_section.strip("<")

    # ---------------------------------------------------------
    # Name
    # ---------------------------------------------------------

    name_parts = [
        part.strip()
        for part in name_section.split("<")
        if part.strip()
    ]

    surname = ""
    given_names = ""

    if name_parts:
        surname = name_parts[0]

    if len(name_parts) > 1:
        given_names = " ".join(name_parts[1:])

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return {
        "document_type": document_type,
        "country": country,
        "surname": surname,
        "given_names": given_names,
        "passport_number": passport_number,
        "nationality": nationality,
        "date_of_birth": parse_mrz_date(birth_date_raw),
        "sex": sex,
        "date_of_expiry": parse_mrz_date(expiry_date_raw, expiry=True),
    }

def parse_mrz_date(value: str, expiry: bool = False) -> str | None:
    if len(value) != 6 or not value.isdigit():
        return None

    year = int(value[:2])
    month = value[2:4]
    day = value[4:6]

    # MRZ uses two-digit years.
    # 00-26 -> 2000-2026
    # 27-99 -> 1927-1999

    # تاريخ الانتهاء دائماً في القرن الحالي (جواز ينتهي 2030 يُكتب 30 وليس 1930)
    if expiry or year <= 26:
        full_year = 2000 + year
    else:
        full_year = 1900 + year

    return f"{full_year:04d}-{month}-{day}"