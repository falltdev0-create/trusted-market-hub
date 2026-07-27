"""
سكريبت تحميل البيانات من المصادر الموثوقة
"""
import os
import requests
import zipfile
from pathlib import Path

DATASETS_DIR = Path(__file__).parent / "datasets"
DATASETS_DIR.mkdir(exist_ok=True)

SOURCES = {
    "property_prices": {
        "url": "https://www.kaggle.com/api/v1/datasets/download/nehalbirpatel/house-price-prediction-challenge",
        "destination": "datasets/property_prices.zip",
        "type": "kaggle"
    },
    "vehicle_prices": {
        "url": "https://www.kaggle.com/api/v1/datasets/download/hellbuoy/car-price-prediction",
        "destination": "datasets/vehicle_prices.zip",
        "type": "kaggle"
    },
    "property_images": {
        "url": "https://download.pytorch.org/tutorial/hymenoptera_data.zip",
        "destination": "datasets/property_images.zip",
        "type": "direct"
    }
}

def download_kaggle_dataset(url: str, destination: str):
    """تحميل dataset من Kaggle (يتطلب API key)"""
    # ستحتاج إلى تعيين KAGGLE_USERNAME و KAGGLE_KEY في البيئة
    print(f"⚠️  لتحميل بيانات Kaggle، تحتاج إلى:")
    print("  1. حساب Kaggle مجاني")
    print("  2. API key من: kaggle.com/account")
    print("  3. حفظه في ~/.kaggle/kaggle.json")
    print("\nالتعليمات: https://github.com/Kaggle/kaggle-api#api-credentials")

def download_file(url: str, destination: str):
    """تحميل ملف من رابط مباشر"""
    print(f"📥 جاري التحميل من: {url}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    if destination.endswith('.zip'):
        print(f"📦 فك الضغط...")
        with zipfile.ZipFile(destination, 'r') as zip_ref:
            zip_ref.extractall(DATASETS_DIR)

def main():
    print("🔄 بدء تحميل البيانات الموثوقة...")
    
    for name, config in SOURCES.items():
        print(f"\n📊 {name}")
        destination = Path(config['destination'])
        
        if destination.exists():
            print(f"✅ البيانات موجودة فعلاً في {destination}")
            continue
        
        if config['type'] == 'kaggle':
            download_kaggle_dataset(config['url'], config['destination'])
        else:
            download_file(config['url'], config['destination'])

if __name__ == "__main__":
    main()