from app.services.kyc.mrz_parser import (
    find_valid_mrz_line2,
    parse_passport_mrz,
)


texts = [
    "CSDNMOHAMED<ABDALLA<ABDELAAL<MOHAMED<<",
    "026055168SDN8807021M2012191<<<<<<<<<<<",
]


print("MRZ candidates:")

for text in texts:
    print(text)


line2 = find_valid_mrz_line2(texts)

print("\nValid MRZ line 2:")
print(line2)


if line2:
    data = parse_passport_mrz(
        texts[0],
        line2,
    )

    print("\nPassport data:")

    for key, value in data.items():
        print(f"{key}: {value}")