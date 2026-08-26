"""Build 64x64 terrain tiles and tree sprites from generated atlases."""

from pathlib import Path
import sys

from PIL import Image


TERRAIN_NAMES = (
    "terrain_grass",
    "terrain_dirt",
    "terrain_road",
    "terrain_sand",
    "terrain_water",
    "terrain_moss",
    "terrain_rubble",
    "terrain_mud",
)

TREE_NAMES = ("tree_oak", "tree_willow", "tree_dead", "tree_fir")


def _cell(image: Image.Image, column: int, row: int, columns: int, rows: int) -> Image.Image:
    left = round(column * image.width / columns)
    right = round((column + 1) * image.width / columns)
    top = round(row * image.height / rows)
    bottom = round((row + 1) * image.height / rows)
    return image.crop((left, top, right, bottom))


def build_terrain(source: Path, output_directory: Path) -> None:
    atlas = Image.open(source).convert("RGBA")
    for index, name in enumerate(TERRAIN_NAMES):
        tile = _cell(atlas, index % 4, index // 4, 4, 2)
        tile.resize((64, 64), Image.Resampling.NEAREST).save(output_directory / f"{name}.png")


def build_trees(source: Path, output_directory: Path) -> None:
    atlas = Image.open(source).convert("RGBA")
    for index, name in enumerate(TREE_NAMES):
        tree = _cell(atlas, index, 0, 4, 1)
        tree.thumbnail((60, 60), Image.Resampling.NEAREST)
        canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        canvas.alpha_composite(tree, ((64 - tree.width) // 2, 64 - tree.height))
        canvas.save(output_directory / f"{name}.png")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: build_environment_sprites.py TERRAIN_ATLAS TREE_ATLAS OUTPUT_DIRECTORY"
        )
    output = Path(sys.argv[3])
    output.mkdir(parents=True, exist_ok=True)
    build_terrain(Path(sys.argv[1]), output)
    build_trees(Path(sys.argv[2]), output)
