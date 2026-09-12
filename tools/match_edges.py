from PIL import Image
from pathlib import Path

scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")
top_left = Image.open(scratch / "lake_top_left.png").convert("RGB")

for name in ("north", "south", "west", "east", "north_west", "north_east", "south_west", "south_east"):
    edge = Image.open(scratch / f"edge_{name}_0.png").convert("RGB")
    min_diff = float("inf")
    best_pos = None
    for y in range(top_left.height - 32):
        for x in range(top_left.width - 32):
            diff = 0
            for py in range(0, 32, 2):
                for px in range(0, 32, 2):
                    c1 = top_left.getpixel((x + px, y + py))
                    c2 = edge.getpixel((px, py))
                    diff += sum(abs(a - b) for a, b in zip(c1, c2))
            if diff < min_diff:
                min_diff = diff
                best_pos = (x, y)
    print(f"{name:12s}: best_pos={best_pos}, diff={min_diff}")
