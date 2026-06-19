from pathlib import Path
from PIL import Image, ImageDraw
import random

base = Path('dataset')
for split in ['train', 'val']:
    for label in ['excellent', 'good', 'poor']:
        p = base / split / label
        p.mkdir(parents=True, exist_ok=True)
        count = 12 if split == 'train' else 4
        for i in range(count):
            img = Image.new('RGB', (480, 480), (255, 255, 255))
            draw = ImageDraw.Draw(img)
            fill = (30, 144, 255) if label == 'excellent' else ((34, 139, 34) if label == 'good' else (178, 34, 34))
            for j in range(5):
                x0 = random.randint(0, 360)
                y0 = random.randint(0, 360)
                x1 = random.randint(x0 + 20, 480)
                y1 = random.randint(y0 + 20, 480)
                shape = [x0, y0, x1, y1]
                draw.ellipse(shape, outline=fill, width=15)
            draw.text((20, 20), f"{label} {i+1}", fill=fill)
            img.save(p / f"{label}_{i+1}.jpg")
print('dataset generated')
