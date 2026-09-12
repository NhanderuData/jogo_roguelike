import sys
from pathlib import Path
from PIL import Image

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa
from graphics.renderer import Renderer
from core.camera import Camera

ctx = GameContext(
    input=InputManager(),
    content=ContentCatalog.load_default(),
    audio=NullSoundManager(),
)

# Search seeds where a pond has a water tile with land north and land west,
# or let's check for any lake in seed 0..30 where a water tile has land north & west
for s in range(50):
    mapa = Mapa(ctx, seed=s)
    cam = Camera()
    renderer = Renderer(cam)
    for y in range(mapa.altura):
        for x in range(mapa.largura):
            t = mapa.obter_tile(x, y)
            if t and t.tipo == "deep_water" and t.bioma == "lagoa":
                # Check neighbors
                edge = renderer._pond_edge_name(mapa, x, y)
                n = mapa.obter_tile(x, y-1)
                w = mapa.obter_tile(x-1, y)
                n_land = n and n.tipo not in {"deep_water", "bridge"}
                w_land = w and w.tipo not in {"deep_water", "bridge"}
                if n_land and w_land and edge != "north_west":
                    print(f"Seed {s}: tile at ({x}, {y}) has N_land={n_land}, W_land={w_land}, but edge={edge}")
print("Done scan.")
