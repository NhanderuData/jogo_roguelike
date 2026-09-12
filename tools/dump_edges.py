import sys
from pathlib import Path
from PIL import Image

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from graphics import recursos
recursos.carregar_tudo()

def check():
    top_left = Image.open(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch\lake_top_left.png")
    # Save the 8 edge sprites from recursos for comparison
    scratch = Path(r"C:\Users\rafae\.gemini\antigravity-ide\brain\bb1cab2e-6a0d-4418-adf7-05992c55c32f\scratch")
    for name in ("north", "south", "west", "east", "north_west", "north_east", "south_west", "south_east"):
        frames = recursos.SPRITES[f"terrain_pond_edge_{name}_frames"]
        for i, frame in enumerate(frames):
            pygame.image.save(frame, str(scratch / f"edge_{name}_{i}.png"))
    print("Saved edge frames to scratch")

if __name__ == "__main__":
    check()
