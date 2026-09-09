import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image
from graphics import recursos


class SpriteAssetTests(unittest.TestCase):
    def test_image_loader_reuses_the_same_atlas(self):
        fake_image = Mock()
        fake_image.convert_alpha.return_value = fake_image
        recursos._IMAGE_CACHE.clear()
        with patch.object(recursos.pygame.image, "load", return_value=fake_image) as load:
            first = recursos._carregar_imagem("sprites/fake-atlas.png")
            second = recursos._carregar_imagem("sprites/fake-atlas.png")

        self.assertIs(first, second)
        load.assert_called_once()
        recursos._IMAGE_CACHE.clear()

    def test_content_sprite_references_are_validated(self):
        content = SimpleNamespace(
            items={"item": SimpleNamespace(sprite="known")},
            entities={"entity": SimpleNamespace(sprite="missing")},
            weapons={},
        )
        previous = dict(recursos.SPRITES)
        recursos.SPRITES.clear()
        recursos.SPRITES["known"] = object()
        try:
            with self.assertRaisesRegex(RuntimeError, "missing"):
                recursos.validar_sprites_conteudo(content)
        finally:
            recursos.SPRITES.clear()
            recursos.SPRITES.update(previous)

    def test_pixel_crawler_animation_sheets_and_license_are_present(self):
        directory = (
            Path(__file__).resolve().parents[1]
            / "assets" / "sprites" / "pixel_crawler"
        )
        expected_sizes = {
            "player_idle_down.png": (256, 64),
            "player_idle_side.png": (256, 64),
            "player_idle_up.png": (256, 64),
            "player_run_down.png": (384, 64),
            "player_run_side.png": (384, 64),
            "player_run_up.png": (384, 64),
            "skeleton_idle.png": (128, 32),
            "skeleton_run.png": (384, 64),
            "orc_rogue_idle.png": (128, 32),
            "orc_rogue_run.png": (384, 64),
            "orc_warrior_idle.png": (128, 32),
            "orc_warrior_run.png": (384, 64),
        }

        self.assertTrue((directory / "LICENSE.txt").is_file())
        for filename, size in expected_sizes.items():
            with Image.open(directory / filename) as image:
                self.assertEqual(image.size, size, filename)

    def test_pixel_crawler_nature_atlases_are_present(self):
        directory = (
            Path(__file__).resolve().parents[1]
            / "assets" / "sprites" / "pixel_crawler" / "nature"
        )
        expected_sizes = {
            "floors.png": (400, 416),
            "farm.png": (400, 400),
            "building_props.png": (400, 400),
            "bonfire_sheet.png": (128, 32),
            "dungeon_tiles.png": (400, 400),
            "water.png": (400, 400),
            "rocks.png": (208, 304),
            "vegetation.png": (400, 432),
            "trees_broad.png": (256, 128),
            "trees_broad_large.png": (368, 256),
            "trees_conifer_large.png": (192, 224),
            "trees_round.png": (128, 96),
            "trees_fir.png": (128, 160),
        }

        for filename, size in expected_sizes.items():
            with Image.open(directory / filename) as image:
                self.assertEqual(image.size, size, filename)
                self.assertEqual(image.mode, "RGBA", filename)

    def test_generated_item_sprites_are_64px_rgba(self):
        directory = Path(__file__).resolve().parents[1] / "assets" / "sprites"
        sprites = [
            path
            for path in directory.glob("*.png")
            if path.name.startswith(("weapon_", "item_"))
        ]
        self.assertEqual(len(sprites), 8)

        for path in sprites:
            with Image.open(path) as image:
                self.assertEqual(image.size, (64, 64), path.name)
                self.assertEqual(image.mode, "RGBA", path.name)
                self.assertEqual(image.getpixel((0, 0))[3], 0, path.name)

    def test_environment_sprites_are_64px(self):
        directory = Path(__file__).resolve().parents[1] / "assets" / "sprites"
        sprites = [
            path
            for path in directory.glob("*.png")
            if path.name.startswith(("terrain_", "tree_"))
        ]
        self.assertEqual(len(sprites), 12)

        for path in sprites:
            with Image.open(path) as image:
                self.assertEqual(image.size, (64, 64), path.name)
                self.assertEqual(image.mode, "RGBA", path.name)

        for path in directory.glob("tree_*.png"):
            with Image.open(path) as image:
                self.assertEqual(image.getpixel((0, 0))[3], 0, path.name)



if __name__ == "__main__":
    unittest.main()
