import sys
from pathlib import Path

# Add src to path
src_dir = Path("src").resolve()
sys.path.insert(0, str(src_dir))

from core.context import GameContext
from core.input_manager import InputManager
from core.content import ContentCatalog
from core.audio import NullSoundManager
from map.map_gen import Mapa
from graphics.renderer import Renderer
from core.camera import Camera

def main():
    ctx = GameContext(
        input=InputManager(),
        content=ContentCatalog.load_default(),
        audio=NullSoundManager(),
    )

    # Generate map
    mapa = Mapa(ctx, seed=1337)
    cam = Camera()
    renderer = Renderer(cam)

    print(f"Number of ponds: {len(mapa.ponds)}")
    for i, pond in enumerate(mapa.ponds):
        cx, cy = pond.centro
        rx, ry = pond.raios
        print(f"\n--- Pond {i}: center=({cx}, {cy}), radii=({rx}, {ry}) ---")
        # Let's inspect the bounding box of the pond
        x0, x1 = max(0, cx - rx - 3), min(mapa.largura, cx + rx + 4)
        y0, y1 = max(0, cy - ry - 3), min(mapa.altura, cy + ry + 4)

        for y in range(y0, y1):
            line_types = []
            line_edges = []
            for x in range(x0, x1):
                tile = mapa.obter_tile(x, y)
                if not tile:
                    line_types.append(" ")
                    line_edges.append("  ")
                    continue
                if tile.tipo == "deep_water" and tile.bioma == "lagoa":
                    edge = renderer._pond_edge_name(mapa, x, y)
                    if edge:
                        short = {
                            "north": "N ",
                            "south": "S ",
                            "west": "W ",
                            "east": "E ",
                            "north_west": "NW",
                            "north_east": "NE",
                            "south_west": "SW",
                            "south_east": "SE",
                        }.get(edge, "??")
                        line_types.append("~")
                        line_edges.append(short)
                    else:
                        line_types.append("~")
                        line_edges.append("..") # interior water
                elif tile.tipo == "deep_water":
                    line_types.append("w") # other water
                    line_edges.append("ww")
                elif tile.tipo == "grass":
                    line_types.append("#")
                    line_edges.append("##")
                elif tile.tipo == "terra":
                    line_types.append("t")
                    line_edges.append("tt")
                else:
                    line_types.append(tile.tipo[0])
                    line_edges.append(tile.tipo[:2])
            print("".join(line_types) + "    " + "".join(line_edges))

if __name__ == "__main__":
    main()
