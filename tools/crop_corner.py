from PIL import Image
from pathlib import Path

scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")
top_left = Image.open(scratch / "lake_top_left.png").convert("RGB")

# Let's crop (x=60, y=20, size=32) and (x=28, y=52, size=32)
# Wait, remember x=79 and y=31 in inspect_spans earlier!
# In inspect_spans:
# y=31..53: blue x in [79, 149]!
# So the sharp horizontal line is at y=31!
# And the vertical edge is at x=79!
# That means the tile at (79, 31) has width 32 (79..111) and height 32 (31..63)!
tile_corner = top_left.crop((79, 31, 79+32, 31+32))
tile_corner.save(scratch / "tile_corner_79_31.png")

# And what is at (79-32, 31): (47, 31)
tile_west_of_it = top_left.crop((79-32, 31, 79, 31+32))
tile_west_of_it.save(scratch / "tile_west_47_31.png")

# And what is at (79, 31-32): (79, -1) -> (79, 0..31)
tile_north_of_it = top_left.crop((79, 0, 79+32, 32))
tile_north_of_it.save(scratch / "tile_north_79_0.png")

print("Saved tile_corner_79_31, tile_west, tile_north")
