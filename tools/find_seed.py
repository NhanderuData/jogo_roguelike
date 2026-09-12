import sys
from pathlib import Path

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa

# In the screenshot, let's find the dimensions of the lake:
# Width of the lake in tiles:
# In the screenshot earlier, water was ~10 tiles wide and ~10 tiles high.
# Let's search seeds to find a pond with rx ~ 5..6, ry ~ 5..6

def search():
    ctx = GameContext(
        input=InputManager(),
        content=ContentCatalog.load_default(),
        audio=NullSoundManager(),
    )
    # Let's test seeds: maybe 0, 1, 42, 1337, or random
    for seed in range(200):
        mapa = Mapa(ctx, seed=seed)
        for pond in mapa.ponds:
            rx, ry = pond.raios
            if 4 <= rx <= 6 and 4 <= ry <= 6:
                print(f"Seed {seed}: pond at {pond.centro} radii=({rx}, {ry})")

if __name__ == "__main__":
    search()
