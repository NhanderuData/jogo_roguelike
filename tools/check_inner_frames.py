from PIL import Image

im = Image.open("assets/sprites/pixel_crawler/nature/water.png")

inner_offsets = {
    "inner_north_west": (48, 64),
    "inner_north_east": (16, 64),
    "inner_south_west": (48, 0),
    "inner_south_east": (16, 0),
}

for name, (ox, oy) in inner_offsets.items():
    print(f"Checking {name}:")
    for frame in range(4):
        fx = ox + frame * 96
        fy = oy
        tile = im.crop((fx, fy, fx + 16, fy + 16))
        # Check non-transparent
        extrema = tile.getextrema()
        print(f"  Frame {frame} at ({fx}, {fy}): extrema={extrema[3]}")
