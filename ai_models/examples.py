"""
Usage Examples — Maskan AI Models v2

Demonstrates all three models in real-world scenarios.
"""

from ai_models_hf import ConditionPredictor, DocumentMatcher, PricingPredictor


# ══════════════════════════════════════════════════════════════════════════════
# Example 1: Property Condition Assessment
# ══════════════════════════════════════════════════════════════════════════════

def example_condition_assessment():
    """Assess the condition of a property from photos."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Property Condition Assessment")
    print("="*70)

    # Initialize predictor
    predictor = ConditionPredictor()

    # Load images (in real scenario, from user upload)
    # with open("house_photo_1.jpg", "rb") as f:
    #     img1 = f.read()
    # with open("house_photo_2.jpg", "rb") as f:
    #     img2 = f.read()

    # For demo, create dummy images (this won't work, just shows structure)
    # In production, use real images
    images = []  # [img1, img2]

    if not images:
        print("\n⚠️  Skipping condition assessment (no demo images available)")
        print("   In production, load real images from user upload:")
        print("   >>> with open('house_photo.jpg', 'rb') as f: img = f.read()")
        print("   >>> result = predictor.predict([img], category='house')")
        return

    # Make prediction
    result = predictor.predict(images, category="house")

    # Display results
    print(f"\n📊 ASSESSMENT RESULTS")
    print(f"━━━━━━━━━━━━━━━━━━━━━")
    print(f"Grade: {result['grade_ar']} ({result['grade_en']})")
    print(f"Score: {result['score']}/100")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Uncertainty: ±{result['uncertainty']:.2%}")
    print(f"Images analyzed: {result['images_analyzed']}")

    print(f"\n📋 DETAILED CRITERIA")
    print(f"━━━━━━━━━━━━━━━━━")
    for criterion in result.get('criteria_scores', [])[:4]:  # Show first 4
        ar_name = criterion['criterion'].split(' | ')[0]
        print(f"  • {ar_name}: {criterion['score']:.0f}/100 ({criterion['grade']})")

    print(f"\n💡 RECOMMENDATIONS")
    print(f"━━━━━━━━━━━━━━━")
    for rec in result.get('recommendations', [])[:3]:
        print(f"  {rec}")

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Example 2: Document Verification
# ══════════════════════════════════════════════════════════════════════════════

def example_document_verification():
    """Verify that ID and ownership documents match."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Document Verification")
    print("="*70)

    # Initialize matcher
    matcher = DocumentMatcher()

    # Load documents (in real scenario, from user upload)
    # with open("id_card.jpg", "rb") as f:
    #     id_doc = f.read()
    # with open("ownership_cert.jpg", "rb") as f:
    #     own_doc = f.read()

    # For demo purposes
    print("\n📋 SETUP")
    print("━━━━━━━")
    print("In production, load real documents:")
    print("  >>> with open('id_card.jpg', 'rb') as f: id_doc = f.read()")
    print("  >>> with open('ownership.jpg', 'rb') as f: own_doc = f.read()")
    print("  >>> result = matcher.match(id_doc, own_doc, category='house')")

    # Simulate demo result
    print("\n✅ VERIFICATION RESULTS (Demo)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Status: ✅ PASS")
    print(f"Overall Score: 85.0/100")
    print(f"Confidence Level: High")
    print(f"Name Match: 88.5/100")
    print(f"Number Match: 95.0/100")

    print(f"\n📝 EXTRACTED INFORMATION")
    print(f"━━━━━━━━━━━━━━━━━━━━")
    print(f"ID Name: محمد أحمد علي")
    print(f"Ownership Name: محمد أحمد علي")
    print(f"ID Number: 123456789")
    print(f"Registration: 123456789")

    print(f"\n✓ No issues found")

    # Return sample result structure
    return {
        "match_score": 85.0,
        "passed": True,
        "status": "✅ PASS",
        "confidence_level": "High",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Example 3: Price Estimation
# ══════════════════════════════════════════════════════════════════════════════

def example_price_estimation():
    """Estimate market price for properties and vehicles."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Price Estimation")
    print("="*70)

    # Initialize pricing model
    pricing = PricingPredictor()

    # Example 1: House for sale
    print("\n🏠 HOUSE PRICE ESTIMATION")
    print("━━━━━━━━━━━━━━━━━━━")

    house_features = {
        "size": 250,              # Square meters
        "bedrooms": 4,
        "year": 2015,             # Construction year
        "city": "الخرطوم",        # Khartoum
    }

    house_result = pricing.predict(
        category="house",
        listing_type="sale",
        condition_grade="good",
        features=house_features
    )

    print(f"Category: House")
    print(f"Type: Sale")
    print(f"Condition: Good (Good)")
    print(f"Size: 250 m²")
    print(f"City: الخرطوم (Khartoum)")
    print(f"\n💰 PRICE ESTIMATE")
    print(f"  Suggested: {house_result['suggested_price']:,} SDG")
    print(f"  Range: {house_result['price_range'][0]:,} - {house_result['price_range'][1]:,} SDG")
    print(f"  Confidence: {house_result['confidence_level']}")
    print(f"  Method: {house_result['method']}")

    # Example 2: Car for sale
    print("\n\n🚗 CAR PRICE ESTIMATION")
    print("━━━━━━━━━━━━━━━━━━")

    car_features = {
        "year": 2018,             # Model year
        "km": 95_000,             # Kilometers
        "city": "الخرطوم",        # Khartoum
    }

    car_result = pricing.predict(
        category="car",
        listing_type="sale",
        condition_grade="good",
        features=car_features
    )

    print(f"Category: Car")
    print(f"Type: Sale")
    print(f"Condition: Good")
    print(f"Model Year: 2018 (Age: 7 years)")
    print(f"Kilometers: 95,000 km")
    print(f"City: الخرطوم (Khartoum)")
    print(f"\n💰 PRICE ESTIMATE")
    print(f"  Suggested: {car_result['suggested_price']:,} SDG")
    print(f"  Range: {car_result['price_range'][0]:,} - {car_result['price_range'][1]:,} SDG")
    print(f"  Confidence: {car_result['confidence_level']}")

    # Example 3: Apartment for rent
    print("\n\n🏘️ APARTMENT RENT ESTIMATION")
    print("━━━━━━━━━━━━━━━━━━━━")

    apt_features = {
        "size": 120,              # Square meters
        "bedrooms": 2,
        "year": 2010,
        "city": "الخرطوم",
    }

    apt_result = pricing.predict(
        category="house",
        listing_type="rent",
        condition_grade="good",
        features=apt_features
    )

    print(f"Category: Apartment")
    print(f"Type: Rent (monthly)")
    print(f"Condition: Good")
    print(f"Size: 120 m²")
    print(f"Bedrooms: 2")
    print(f"City: الخرطوم")
    print(f"\n💰 MONTHLY RENT")
    print(f"  Suggested: {apt_result['suggested_price']:,} SDG/month")
    print(f"  Range: {apt_result['price_range'][0]:,} - {apt_result['price_range'][1]:,} SDG/month")

    return {
        "house_sale": house_result,
        "car_sale": car_result,
        "apartment_rent": apt_result,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Example 4: Complete Listing Analysis
# ══════════════════════════════════════════════════════════════════════════════

def example_complete_listing_analysis():
    """Complete analysis of a property listing (all models together)."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Complete Listing Analysis Workflow")
    print("="*70)

    print("\n🔄 WORKFLOW FOR NEW PROPERTY LISTING")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    print("\nStep 1️⃣: ASSESS CONDITION")
    print("  • User uploads 3-5 property photos")
    print("  • System analyzes condition (poor/good/excellent)")
    print("  • Generates detailed assessment report")
    print("  ✓ Grade: Excellent | Score: 88.5/100")

    print("\nStep 2️⃣: VERIFY OWNERSHIP")
    print("  • User uploads ID and ownership documents")
    print("  • System extracts text via OCR")
    print("  • Matches names and document numbers")
    print("  ✓ Status: PASS | Confidence: High")

    print("\nStep 3️⃣: ESTIMATE MARKET PRICE")
    print("  • System receives property details (size, bedrooms, etc.)")
    print("  • Calculates price based on condition grade and market data")
    print("  • Provides price range with confidence level")
    print("  ✓ Suggested: 1,080,000 SDG | Range: 918k-1.24M SDG")

    print("\nStep 4️⃣: LIST PROPERTY")
    print("  • Create listing with:")
    print("    - Condition grade from assessment")
    print("    - Verified documents")
    print("    - AI-suggested price")
    print("    - Automated recommendations")

    print("\n✅ LISTING READY FOR MARKET")
    print("━━━━━━━━━━━━━━━━━━━━━━")
    print("The property is now:")
    print("  ✓ Condition verified")
    print("  ✓ Ownership confirmed")
    print("  ✓ Fairly priced")
    print("  ✓ Ready to attract buyers")


# ══════════════════════════════════════════════════════════════════════════════
# Integration Example: FastAPI
# ══════════════════════════════════════════════════════════════════════════════

def example_fastapi_integration():
    """Example of integrating models into FastAPI backend."""
    print("\n" + "="*70)
    print("EXAMPLE 5: FastAPI Integration")
    print("="*70)

    code = '''
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
from ai_models_hf import ConditionPredictor, DocumentMatcher, PricingPredictor

app = FastAPI(title="Maskan AI API")

# Initialize models at startup
condition_model = ConditionPredictor()
doc_model = DocumentMatcher()
pricing_model = PricingPredictor()

# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/listings/{listing_id}/assess-condition")
async def assess_condition(listing_id: str, images: List[UploadFile], category: str = "house"):
    """Assess property/vehicle condition from images."""
    try:
        image_bytes = [await f.read() for f in images]
        result = condition_model.predict(image_bytes, category)
        return {"listing_id": listing_id, "assessment": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/listings/{listing_id}/verify-documents")
async def verify_documents(listing_id: str, id_doc: UploadFile, ownership_doc: UploadFile):
    """Verify ID and ownership documents match."""
    try:
        id_bytes = await id_doc.read()
        own_bytes = await ownership_doc.read()
        result = doc_model.match(id_bytes, own_bytes)
        return {"listing_id": listing_id, "verification": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────

class PricingRequest(BaseModel):
    category: str          # "house" or "car"
    listing_type: str      # "sale" or "rent"
    condition_grade: str   # "poor", "good", "excellent"
    features: dict         # size, bedrooms, year, km, city, etc.

@app.post("/api/v1/estimate-price")
async def estimate_price(request: PricingRequest):
    """Estimate market price."""
    try:
        result = pricing_model.predict(
            request.category,
            request.listing_type,
            request.condition_grade,
            request.features
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─────────────────────────────────────────────────────────────────────────────

@app.post("/api/v1/listings/analyze")
async def analyze_listing(
    category: str,
    listing_type: str,
    images: List[UploadFile],
    id_doc: UploadFile,
    ownership_doc: UploadFile,
    features: dict
):
    """Complete listing analysis in one request."""
    try:
        # Step 1: Assess condition
        image_bytes = [await f.read() for f in images]
        condition = condition_model.predict(image_bytes, category)
        
        # Step 2: Verify documents
        id_bytes = await id_doc.read()
        own_bytes = await ownership_doc.read()
        verification = doc_model.match(id_bytes, own_bytes, category)
        
        # Step 3: Estimate price
        pricing = pricing_model.predict(
            category,
            listing_type,
            condition['grade'],
            features
        )
        
        return {
            "condition": condition,
            "verification": verification,
            "pricing": pricing,
            "ready_to_list": verification['passed'] and condition['score'] >= 50
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
'''

    print(code)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    print("\n" + "█"*70)
    print("█ Maskan AI Models v2 — Usage Examples")
    print("█"*70)

    # Run examples
    try:
        example_condition_assessment()
    except Exception as e:
        print(f"Note: {e}")

    try:
        example_document_verification()
    except Exception as e:
        print(f"Note: {e}")

    example_price_estimation()
    example_complete_listing_analysis()
    example_fastapi_integration()

    print("\n" + "█"*70)
    print("█ Examples complete! Ready to integrate into your application")
    print("█"*70 + "\n")
