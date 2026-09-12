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

cardinais = {
    "north": (0, -1),
    "south": (0, 1),
    "west": (-1, 0),
    "east": (1, 0),
}
opostos = ({"north", "south"}, {"west", "east"})

for seed in range(3):
    mapa = Mapa(ctx, seed=seed)

    # Check all deep_water lagoa tiles
    for y in range(mapa.altura):
        for x in range(mapa.largura):
            tile = mapa.obter_tile(x, y)
            if not tile or tile.tipo != "deep_water" or tile.bioma != "lagoa":
                continue
            terra = set()
            for lado, (dx, dy) in cardinais.items():
                v = mapa.obter_tile(x + dx, y + dy)
                if v and v.tipo not in {"deep_water", "bridge"}:
                    terra.add(lado)
            if len(terra) >= 3 or any(par <= terra for par in opostos):
                print(f"Seed {seed}: tile at ({x}, {y}) still has terra={terra}!")
print("Done check.")
