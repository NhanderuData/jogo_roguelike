from PIL import Image
from pathlib import Path

im = Image.open("assets/sprites/pixel_crawler/nature/water.png")
scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")

inner_offsets = {
    "inner_north_west": (48, 64),
    "inner_north_east": (16, 64),
    "inner_south_west": (48, 0),
    "inner_south_east": (16, 0),
}

for name, (ox, oy) in inner_offsets.items():
    tile = im.crop((ox, oy, ox + 16, oy + 16))
    tile_2x = tile.resize((32, 32), Image.Resampling.NEAREST)
    tile_2x.save(scratch / f"{name}.png")
    print(f"Saved {name}.png")
