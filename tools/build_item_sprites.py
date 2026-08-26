"""Build 64x64 transparent item sprites from the generated 4x2 atlas."""

from pathlib import Path
import sys

from PIL import Image


SPRITES = (
    "weapon_pistol",
    "weapon_shotgun",
    "weapon_smg",
    "weapon_machete",
    "item_medkit",
    "item_energy_drink",
    "item_armor",
    "item_ammo_box",
)


def build(source: Path, output_directory: Path) -> None:
    atlas = Image.open(source).convert("RGBA")
    output_directory.mkdir(parents=True, exist_ok=True)

    for index, name in enumerate(SPRITES):
        column = index % 4
        row = index // 4
        left = round(column * atlas.width / 4)
        right = round((column + 1) * atlas.width / 4)
        top = round(row * atlas.height / 2)
        bottom = round((row + 1) * atlas.height / 2)
        sprite = atlas.crop((left, top, right, bottom))
        sprite.thumbnail((60, 60), Image.Resampling.NEAREST)

        canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        x = (64 - sprite.width) // 2
        y = (64 - sprite.height) // 2
        canvas.alpha_composite(sprite, (x, y))
        canvas.save(output_directory / f"{name}.png")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: build_item_sprites.py SOURCE_ATLAS OUTPUT_DIRECTORY")
    build(Path(sys.argv[1]), Path(sys.argv[2]))
