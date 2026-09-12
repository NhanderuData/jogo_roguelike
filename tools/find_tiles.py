from pathlib import Path
from PIL import Image

def split():
    top_left = Image.open(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch\lake_top_left.png")
    scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")
    
    # top_left size is (150, 160)
    # The water boundary top edge has shore at y around 16..20.
    # Let's find the exact 32x32 grid
    # Let's crop candidate 32x32 tiles
    # In edge_west_0, width is 32, height is 32.
    # Let's find matches of edge_west_0 in top_left!
    edge_west = Image.open(scratch / "edge_west_0.png").convert("RGB")
    # Search position of edge_west in top_left:
    min_diff = float("inf")
    best_pos = None
    for y in range(top_left.height - 32):
        for x in range(top_left.width - 32):
            diff = 0
            for py in range(32):
                for px in range(32):
                    c1 = top_left.getpixel((x + px, y + py))
                    c2 = edge_west.getpixel((px, py))
                    diff += sum(abs(a - b) for a, b in zip(c1, c2))
            if diff < min_diff:
                min_diff = diff
                best_pos = (x, y)
    print(f"Best match for edge_west_0: pos={best_pos}, diff={min_diff}")
    
    # Also search edge_north_0
    edge_north = Image.open(scratch / "edge_north_0.png").convert("RGB")
    min_diff_n = float("inf")
    best_pos_n = None
    for y in range(top_left.height - 32):
        for x in range(top_left.width - 32):
            diff = 0
            for py in range(32):
                for px in range(32):
                    c1 = top_left.getpixel((x + px, y + py))
                    c2 = edge_north.getpixel((px, py))
                    diff += sum(abs(a - b) for a, b in zip(c1, c2))
            if diff < min_diff_n:
                min_diff_n = diff
                best_pos_n = (x, y)
    print(f"Best match for edge_north_0: pos={best_pos_n}, diff={min_diff_n}")

if __name__ == "__main__":
    split()
