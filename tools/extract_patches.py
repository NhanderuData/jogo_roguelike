from pathlib import Path
from PIL import Image

def extract():
    src = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\.user_uploaded\media_1789176549092.png")
    im = Image.open(src).convert("RGB")
    scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")
    scratch.mkdir(exist_ok=True)

    # Let's save patches of the lake borders:
    # 1. Top-left corner
    patch_tl = im.crop((50, 40, 200, 200))
    patch_tl.save(scratch / "lake_top_left.png")

    # 2. Left edge
    patch_left = im.crop((50, 150, 200, 320))
    patch_left.save(scratch / "lake_left.png")

    # 3. Bottom tip
    patch_bot = im.crop((180, 280, 320, 420))
    patch_bot.save(scratch / "lake_bottom.png")

    # 4. Right edge
    patch_right = im.crop((300, 100, 440, 280))
    patch_right.save(scratch / "lake_right.png")

    # 5. Full lake
    patch_full = im.crop((50, 40, 450, 420))
    patch_full.save(scratch / "lake_full.png")

    print("Patches saved to scratch.")

if __name__ == "__main__":
    extract()
