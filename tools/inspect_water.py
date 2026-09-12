from pathlib import Path
from PIL import Image

def analyze():
    user_img_path = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\.user_uploaded\media_1789176549092.png")
    user_im = Image.open(user_img_path).convert("RGB")
    w, h = user_im.size
    print(f"Screenshot size: {w}x{h}")
    # Water color in game is around (60, 140..150, 200..220)
    # Find the exact grid of the tiles
    # In pure water, pixels are (62, 146, 209) or animated variants
    # Let's search all 32x32 tiles in screenshot
    # Find all tiles where one part is pure water (62, 146, 209) and another part is grass (50, 116, 4)
    # AND there is NO shore transition (shore has brown ~ (159, 108, 63) or foam/waves)
    print("Finding border tiles with sharp cutoff (no shore):")
    # Let's align grid by testing ox in range(32), oy in range(32)
    # The pure water tiles have repetition every 32px.
    # In pure water: (80, 0) scaled 2x -> 32x32 tile.
    # Water in the screenshot is light blue: r ~ 60-80, g ~ 140-160, b ~ 200-225
    water_pixels = []
    for y in range(h):
        for x in range(w):
            r, g, b = user_im.getpixel((x, y))
            if 50 <= r <= 95 and 125 <= g <= 170 and 190 <= b <= 235:
                water_pixels.append((x, y))
    
    if not water_pixels:
        print("No water found with filter")
        return
    # Let's find tile grid offset by looking for 32px repetition of pure water pattern
    # In pure water, there's a 32x32 pattern
    im_water = Image.open("assets/sprites/pixel_crawler/nature/water.png")
    # Let's test grid offsets ox in [0..31], oy in [0..31]
    best_ox, best_oy = None, None
    # Let's find a pure water tile inside the lake, e.g. center of the lake is at x ~ 240, y ~ 200
    # Let's check vertical and horizontal edges in the screenshot:
    # Notice at x=405, or x=77:
    # Let's find vertical lines with high gradient
    print(f"Detecting exact tile grid:")
    # Look at the sharp vertical edge at the left of the lake:
    # In the screenshot, let's find the x coordinate of that sharp straight edge:
    # In the screenshot, let's test grid origins (gx, gy) with step 32
    # The water bounds were x=[77, 405], y=[57, 387]
    # 405 - 77 = 328, 328 / 32 = 10.25 tiles.
    # Let's find the exact tile boundaries.
    # At x=79 we had a sharp edge. 79 + 32*k: 79, 111, 143, 175, 207, 239, 271, 303, 335, 367, 399
    # 399 + 32 = 431.
    # At y, what was the sharp edge? Let's check y=71?
    # 71 + 32*k: 71, 103, 135, 167, 199, 231, 263, 295, 327, 359, 391
    # 71 - 32 = 39. 57 is between 39 and 71.
    # Let's verify each 32x32 block for gx in range(75, 85), gy in range(65, 75)
    # Let's crop the tiles from screenshot and see what was rendered
    # In the screenshot:
    # Row 2, Col 2 (approx x=79, y=71)
    tile_left = user_im.crop((79, 71, 79+32, 71+32))
    tile_above = user_im.crop((79+32, 71-32, 79+64, 71))
    tile_corner = user_im.crop((79, 71-32, 79+32, 71))
    print("Tile at (79, 71) [Row 2, Col 2]:")
    print("Left 4 cols of pixels:")
    for py in range(0, 32, 4):
        print([tile_left.getpixel((px, py)) for px in range(0, 8, 2)])
    print("Right 4 cols of pixels:")
    for py in range(0, 32, 4):
        print([tile_left.getpixel((px, py)) for px in range(24, 32, 2)])
    return








    # Let's inspect the tiles in the 6x6 grid (0..80, 0..80)
    # Check pixels at borders: top, bottom, left, right to see which borders have shore (brown/foam) vs water vs transparent
    offsets = {
        "north": (32, 64),
        "south": (32, 0),
        "west": (64, 32),
        "east": (0, 32),
        "north_west": (48, 48),
        "north_east": (16, 48),
        "south_west": (48, 16),
        "south_east": (16, 16),
    }
    for name, (ox, oy) in offsets.items():
        tile = im.crop((ox, oy, ox + 16, oy + 16))
        print(f"=== {name} at ({ox}, {oy}) ===")
        for py in range(0, 16, 2):
            row = []
            for px in range(0, 16):
                r, g, b, a = tile.getpixel((px, py))
                if b > 180 and r < 100:
                    row.append("~")
                elif g > 100 and r < 80:
                    row.append("#")
                else:
                    row.append(".")
            print("".join(row))


    # Let's inspect the entire 400x400 water.png
    print(f"Inspecting 400x400 water.png in steps of 96 or 16:")
    # Check each 16x16 tile across the 400x400 image (25x25 tiles)
    grid = []
    for ty in range(0, 400, 16):
        row = []
        for tx in range(0, 400, 16):
            # Sample center and corners of this 16x16 tile
            water_count = 0
            grass_count = 0
            alpha_zero = 0
            other_count = 0
            for py in range(ty, min(ty + 16, 400), 4):
                for px in range(tx, min(tx + 16, 400), 4):
                    r, g, b, a = im.getpixel((px, py))
                    if a < 10:
                        alpha_zero += 1
                    elif b > 180 and r < 100:
                        water_count += 1
                    elif g > 100 and r < 80:
                        grass_count += 1
                    else:
                        other_count += 1
            if alpha_zero >= 12:
                row.append(" ")
            elif grass_count > 10:
                row.append("#") # grass
            elif water_count > 10:
                row.append("~") # water
            elif grass_count > 2 and water_count > 2:
                row.append("X") # mixed grass+water
            else:
                row.append(".") # shore/other
        grid.append("".join(row))
    for r in grid:
        print(r)



if __name__ == "__main__":
    analyze()
