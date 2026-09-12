import sys
from pathlib import Path

src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa

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

def test():
    ctx = GameContext(
        input=InputManager(),
        content=ContentCatalog.load_default(),
        audio=NullSoundManager(),
    )
    mapa = Mapa(ctx, seed=1337)
    for i, pond in enumerate(mapa.ponds):
        cx, cy = pond.centro
        rx, ry = pond.raios
        print(f"\n--- Pond {i}: center=({cx}, {cy}) ---")
        x0, x1 = max(0, cx - rx - 2), min(mapa.largura, cx + rx + 3)
        y0, y1 = max(0, cy - ry - 2), min(mapa.altura, cy + ry + 3)

        for y in range(y0, y1):
            row = []
            for x in range(x0, x1):
                t = mapa.obter_tile(x, y)
                if t.tipo == "deep_water" and t.bioma == "lagoa":
                    edge = pond_edge_name(mapa, x, y)
                    short = {
                        "north": "N ", "south": "S ", "west": "W ", "east": "E ",
                        "north_west": "NW", "north_east": "NE",
                        "south_west": "SW", "south_east": "SE",
                        "inner_north_west": "nw", "inner_north_east": "ne",
                        "inner_south_west": "sw", "inner_south_east": "se",
                    }.get(edge, "  ")
                    row.append(short)
                else:
                    row.append("##")
            print(" ".join(row))

if __name__ == "__main__":
    test()
