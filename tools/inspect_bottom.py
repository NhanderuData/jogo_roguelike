from PIL import Image

im = Image.open(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch\lake_bottom.png")
w, h = im.size

print("Inspecting blue pixels in lake_bottom.png:")
for y in range(0, h, 2):
    row_blue = []
    for x in range(0, w, 2):
        r, g, b = im.getpixel((x, y))
        if b > 180 and r < 100:
            row_blue.append(x)
    if row_blue:
        print(f"y={y:3d}: blue x in [{min(row_blue):3d}, {max(row_blue):3d}] width={max(row_blue)-min(row_blue)+1}")
