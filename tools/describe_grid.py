from PIL import Image

im = Image.open("assets/sprites/pixel_crawler/nature/water.png")

print("Grid of 16x16 tiles in frame 0 (x=0..64, y=0..64):")
for y in (0, 16, 32, 48, 64):
    row_desc = []
    for x in (0, 16, 32, 48, 64):
        tile = im.crop((x, y, x+16, y+16))
        # Top edge, bottom edge, left edge, right edge
        def get_type(px, py):
            r, g, b, a = tile.getpixel((px, py))
            if b > 180 and r < 100: return "W"
            if g > 100 and r < 80: return "G"
            return "S"
        # 4 corners and center
        tl = get_type(0, 0)
        tr = get_type(15, 0)
        bl = get_type(0, 15)
        br = get_type(15, 15)
        c = get_type(8, 8)
        row_desc.append(f"({x:2d},{y:2d})[{tl}{tr}{bl}{br}:{c}]")
    print("  ".join(row_desc))
