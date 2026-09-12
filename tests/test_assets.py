import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame
from PIL import Image
from graphics import recursos


class SpriteAssetTests(unittest.TestCase):
    def test_pond_edge_frames_keep_native_32px_size(self):
        atlas = pygame.Surface((400, 400), pygame.SRCALPHA)
        with (
            patch.object(recursos, "_carregar_imagem", return_value=atlas),
            patch.object(
                recursos,
                "carregar_regiao_atlas",
                wraps=recursos.carregar_regiao_atlas,
            ) as loader,
        ):
            pond_edges = recursos.carregar_bordas_lagoa(
                "sprites/pixel_crawler/nature"
            )

        self.assertEqual(len(pond_edges), 12)
        self.assertEqual(
            recursos.POND_EDGE_OFFSETS,
            {
                "north": (32, 64),
                "south": (32, 0),
                "west": (64, 32),
                "east": (0, 32),
                "north_west": (48, 48),
                "north_east": (16, 48),
                "south_west": (48, 16),
                "south_east": (16, 16),
                "inner_north_west": (48, 64),
                "inner_north_east": (16, 64),
                "inner_south_west": (48, 0),
                "inner_south_east": (16, 0),
            },
        )
        self.assertEqual(len(loader.call_args_list), 48)
        for call in loader.call_args_list:
            self.assertEqual(call.args[1][2:], (16, 16))
            self.assertEqual(call.kwargs["escala"], 2.0)

        for edge_name, frames in pond_edges.items():
            with self.subTest(edge=edge_name):
                self.assertEqual(len(frames), 4)
                self.assertTrue(
                    all(frame.get_size() == (32, 32) for frame in frames)
                )

    def test_rocks_fill_exactly_one_world_tile(self):
        atlas = pygame.Surface((208, 304), pygame.SRCALPHA)
        with (
            patch.object(recursos, "_carregar_imagem", return_value=atlas),
            patch.object(
                recursos,
                "carregar_regiao_atlas",
                wraps=recursos.carregar_regiao_atlas,
            ) as loader,
        ):
            rocks = recursos.carregar_rochas(
                "sprites/pixel_crawler/nature"
            )

        self.assertEqual(set(rocks), {"rock", "rock_brown"})
        self.assertEqual(
            recursos.ROCK_REGIONS,
            {
                "rock": (176, 16, 16, 16),
                "rock_brown": (80, 16, 16, 16),
            },
        )
        for call in loader.call_args_list:
            self.assertEqual(call.args[1][2:], (16, 16))
            self.assertEqual(call.kwargs["escala"], 2.0)

        for rock_name, image in rocks.items():
            with self.subTest(rock=rock_name):
                self.assertEqual(image.get_size(), (32, 32))

    def test_village_house_is_composed_at_native_resolution_then_scaled(self):
        door = pygame.Surface((12, 20), pygame.SRCALPHA)
        window = pygame.Surface((12, 12), pygame.SRCALPHA)
        chimney = pygame.Surface((10, 18), pygame.SRCALPHA)
        palette = {
            "contorno": (38, 27, 24, 255),
            "madeira": (91, 57, 38, 255),
            "parede": (181, 143, 96, 255),
            "parede_clara": (220, 184, 128, 255),
            "parede_escura": (132, 91, 61, 255),
            "fundacao": (105, 101, 92, 255),
            "telhado": (139, 57, 43, 255),
            "telhado_claro": (190, 82, 55, 255),
            "telhado_escuro": (82, 37, 34, 255),
        }

        house = recursos.criar_casa_vila(
            door,
            window,
            chimney,
            palette,
            seed=17,
        )

        self.assertEqual(house.get_size(), (192, 176))
        self.assertGreater(pygame.mask.from_surface(house).count(), 0)

        for y in range(0, house.get_height(), 2):
            for x in range(0, house.get_width(), 2):
                reference = house.get_at((x, y))
                block = (
                    house.get_at((x + 1, y)),
                    house.get_at((x, y + 1)),
                    house.get_at((x + 1, y + 1)),
                )
                if any(pixel != reference for pixel in block):
                    self.fail(f"non-uniform 2x2 block at {(x, y)}")

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
