import unittest
from unittest.mock import patch

from map import biomas
from map.map_gen import Mapa
from map.tile import Tile


class DesertBiomeTests(unittest.TestCase):
    def test_desert_uses_existing_sand_terrain(self):
        tile = Tile("grass", bloqueado=True)

        biomas.aplicar_bioma_deserto(None, 0, 0, tile, 50)

        self.assertEqual(tile.tipo, "sand")
        self.assertFalse(tile.bloqueado)

    def test_desert_shape_contains_center_and_rejects_far_tiles(self):
        center = (50, 50)
        radii = (20, 10)

        self.assertTrue(Mapa.dentro_do_deserto(50, 50, center, radii))
        self.assertFalse(Mapa.dentro_do_deserto(80, 50, center, radii))

    def test_noise_makes_the_desert_border_irregular(self):
        center = (50, 50)
        radii = (20, 10)

        self.assertTrue(Mapa.dentro_do_deserto(70, 50, center, radii, 0.0))
        self.assertFalse(Mapa.dentro_do_deserto(70, 50, center, radii, 0.2))


class EnvironmentDecorationTests(unittest.TestCase):
    def test_forest_places_non_blocking_decoration(self):
        tile = Tile("terra", bloqueado=True)

        with patch("map.biomas.random.choice", return_value="nature_sprout"):
            biomas.aplicar_bioma_floresta(None, 0, 0, tile, 20)

        self.assertEqual(tile.tipo, "grass")
        self.assertFalse(tile.bloqueado)
        self.assertEqual(tile.decoracao, "nature_sprout")

    def test_forest_rock_blocks_its_tile(self):
        tile = Tile("grass")

        biomas.aplicar_bioma_floresta(None, 0, 0, tile, 4)

        self.assertEqual(tile.tipo, "rocha")
        self.assertTrue(tile.bloqueado)

    def test_desert_uses_dry_decorations(self):
        tile = Tile("grass")

        with patch("map.biomas.random.choice", return_value="nature_twig"):
            biomas.aplicar_bioma_deserto(None, 0, 0, tile, 5)

        self.assertEqual(tile.decoracao, "nature_twig")

    def test_only_decorations_with_volume_block_movement(self):
        low_vegetation = (
            "nature_bush_green",
            "nature_bush_autumn",
            "nature_leaf_cluster",
            "nature_plant_tall",
            "nature_cattail",
            "nature_dry_leafy",
            "nature_dry_cattail",
        )
        for decoration in low_vegetation:
            with self.subTest(decoration=decoration):
                self.assertFalse(biomas.decoracao_solida(decoration))

        self.assertTrue(biomas.decoracao_solida("nature_stump"))
        self.assertTrue(biomas.decoracao_solida("nature_crystal_blue"))
        self.assertTrue(biomas.decoracao_solida("nature_bonfire"))
        self.assertFalse(biomas.decoracao_solida("nature_flower_white"))
        self.assertFalse(biomas.decoracao_solida("nature_fallen_leaves"))

        tile = Tile("grass")
        tile.decoracao = "nature_bush_green"
        map_obj = Mapa.__new__(Mapa)
        map_obj.obter_tile = lambda _x, _y: tile
        self.assertFalse(map_obj.is_blocked_terrain(0, 0))

        tile.decoracao = "nature_stump"
        self.assertTrue(map_obj.is_blocked_terrain(0, 0))


if __name__ == "__main__":
    unittest.main()
