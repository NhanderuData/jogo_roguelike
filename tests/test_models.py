import unittest

from components.status import StatusComponent
from map.grid import Grid
from core.time_system import TimeSystem


class GridTests(unittest.TestCase):
    def test_configure_tile_sets_blocked_flag(self):
        grid = Grid(2, 2)

        grid.configurar_tile(1, 1, "wall", bloqueado=True)

        tile = grid.obter_tile(1, 1)
        self.assertEqual(tile.tipo, "wall")
        self.assertTrue(tile.bloqueado)


class StatusTests(unittest.TestCase):
    def test_hunger_uses_elapsed_time(self):
        class Entity:
            nome = "player"

            def tomar_dano(self, amount):
                pass

        status = StatusComponent(Entity())
        status.update(4.9)
        self.assertEqual(status.fome, 100)

        status.update(0.1)
        self.assertEqual(status.fome, 99)


class TimeSystemTests(unittest.TestCase):
    def test_night_overlay_stays_light(self):
        time_system = TimeSystem()
        time_system.tempo_total = time_system.duracao_dia * 0.7

        time_system.calcular_cor()

        self.assertLessEqual(time_system.obter_cor()[3], 75)


if __name__ == "__main__":
    unittest.main()
