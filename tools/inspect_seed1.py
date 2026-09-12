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

# In seed 1, inspect tile (124, 123) and its neighbors:
mapa = Mapa(ctx, seed=1)
for dy in range(-2, 3):
    row = []
    for dx in range(-2, 3):
        x, y = 124 + dx, 123 + dy
        t = mapa.obter_tile(x, y)
        row.append(f"{t.tipo[:4]}:{t.bioma[:4] if t.bioma else 'none'}")
    print(" ".join(row))
