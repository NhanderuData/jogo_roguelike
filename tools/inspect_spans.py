from PIL import Image

im = Image.open(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch\lake_top_left.png")
w, h = im.size

# Let's inspect the corner at (x, y) where the flat blue horizontal edge meets the flat vertical edge
# Let's find horizontal lines where blue water starts abruptly below grass:
for y in range(h):
    row_blue = []
    for x in range(w):
        r, g, b = im.getpixel((x, y))
        if b > 180 and r < 100:
            row_blue.append(x)
    if row_blue:
        min_x = min(row_blue)
        max_x = max(row_blue)
        print(f"y={y:3d}: blue x in [{min_x:3d}, {max_x:3d}] (count={len(row_blue)})")
