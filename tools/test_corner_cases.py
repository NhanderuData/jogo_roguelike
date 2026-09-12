import sys
from pathlib import Path

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa

ctx = GameContext(
    input=InputManager(),
    content=ContentCatalog.load_default(),
    audio=NullSoundManager(),
)

for seed in range(20):
    mapa = Mapa(ctx, seed=seed)
    for y in range(mapa.altura):
        for x in range(mapa.largura):
            tile = mapa.obter_tile(x, y)
            if not tile or tile.tipo != "deep_water" or tile.bioma != "lagoa":
                continue
            cardinal_land = set()
            for dx, dy, side in ((0, -1, "N"), (0, 1, "S"), (-1, 0, "W"), (1, 0, "E")):
                v = mapa.obter_tile(x + dx, y + dy)
                if v and v.tipo not in {"deep_water", "bridge"}:
                    cardinal_land.add(side)
            
            # Check inner corner candidates
            diag_land = set()
            for dx, dy, diag, c1, c2 in (
                (-1, -1, "NW", "N", "W"),
                (1, -1, "NE", "N", "E"),
                (-1, 1, "SW", "S", "W"),
                (1, 1, "SE", "S", "E"),
            ):
                v = mapa.obter_tile(x + dx, y + dy)
                if v and v.tipo not in {"deep_water", "bridge"}:
                    if c1 not in cardinal_land and c2 not in cardinal_land:
                        diag_land.add(diag)
            
            if cardinal_land and diag_land:
                print(f"Seed {seed}: ({x},{y}) has cardinal={cardinal_land} AND diag={diag_land}")
            if len(diag_land) > 1:
                print(f"Seed {seed}: ({x},{y}) has MULTIPLE diags: {diag_land}")

print("Done corner check.")
