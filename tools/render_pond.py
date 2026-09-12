import sys
from pathlib import Path

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from graphics import recursos
recursos.carregar_tudo()

# Add the 4 inner corners to recursos.SPRITES
nature_base = "sprites/pixel_crawler/nature"
INNER_OFFSETS = {
    "inner_north_west": (48, 64),
    "inner_north_east": (16, 64),
    "inner_south_west": (48, 0),
    "inner_south_east": (16, 0),
}
for name, (ox, oy) in INNER_OFFSETS.items():
    recursos.SPRITES[f"terrain_pond_edge_{name}_frames"] = [
        recursos.carregar_regiao_atlas(
            f"{nature_base}/water.png",
            (ox + frame * 96, oy, 16, 16),
            escala=2.0,
        )
        for frame in range(4)
    ]

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa
from core import config

def pond_edge_name(mapa_obj, x, y):
    land = set()
    for dx, dy, side in (
        (0, -1, "north"),
        (0, 1, "south"),
        (-1, 0, "west"),
        (1, 0, "east"),
    ):
        neighbor = mapa_obj.obter_tile(x + dx, y + dy)
        if neighbor and neighbor.tipo not in {"deep_water", "bridge"}:
            land.add(side)

    for first, second, name in (
        ("north", "west", "north_west"),
        ("north", "east", "north_east"),
        ("south", "west", "south_west"),
        ("south", "east", "south_east"),
    ):
        if first in land and second in land:
            return name
    for side in ("north", "south", "west", "east"):
        if side in land:
            return side

    for dx, dy, name in (
        (-1, -1, "inner_north_west"),
        (1, -1, "inner_north_east"),
        (-1, 1, "inner_south_west"),
        (1, 1, "inner_south_east"),
    ):
        neighbor = mapa_obj.obter_tile(x + dx, y + dy)
        if neighbor and neighbor.tipo not in {"deep_water", "bridge"}:
            return name

    return None

ctx = GameContext(
    input=InputManager(),
    content=ContentCatalog.load_default(),
    audio=NullSoundManager(),
)
mapa = Mapa(ctx, seed=1337)
pond = mapa.ponds[0]
cx, cy = pond.centro
rx, ry = pond.raios
x0, x1 = cx - rx - 2, cx + rx + 3
y0, y1 = cy - ry - 2, cy + ry + 3
w_tiles = x1 - x0
h_tiles = y1 - y0

surface = pygame.Surface((w_tiles * 32, h_tiles * 32))

grass_img = recursos.SPRITES["terrain_grass"]
for y in range(y0, y1):
    for x in range(x0, x1):
        sx = (x - x0) * 32
        sy = (y - y0) * 32
        t = mapa.obter_tile(x, y)
        if t.tipo == "deep_water" and t.bioma == "lagoa":
            edge = pond_edge_name(mapa, x, y)
            if edge:
                img = recursos.SPRITES[f"terrain_pond_edge_{edge}_frames"][0]
            else:
                img = recursos.SPRITES["terrain_water_variants"][0]
        else:
            img = grass_img
        surface.blit(img, (sx, sy))

pygame.image.save(surface, "C:/Users/rafae/.gemini/antigravity-ide/brain/bb1cab2e-6a0d-4418-adf7-05992c55c32f/scratch/rendered_pond.png")
print("Saved rendered_pond.png")
