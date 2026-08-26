import unittest
from pathlib import Path

from PIL import Image


class SpriteAssetTests(unittest.TestCase):
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
