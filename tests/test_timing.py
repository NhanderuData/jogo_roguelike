import unittest

import pygame

from components.ai import AIComponent
from components.sprite import SpriteComponent
from graphics import recursos


class TimingTests(unittest.TestCase):
    def test_sprite_animation_is_independent_of_frame_rate(self):
        frames = [pygame.Surface((2, 2)) for _ in range(12)]
        recursos.SPRITES["timing_test"] = frames

        class Entity:
            moving = True

        one_update = SpriteComponent(Entity(), "timing_test")
        many_updates = SpriteComponent(Entity(), "timing_test")

        one_update.update(1.0)
        for _ in range(10):
            many_updates.update(0.1)

        self.assertAlmostEqual(one_update.frame_index, many_updates.frame_index)
        recursos.SPRITES.pop("timing_test", None)

    def test_ranged_ai_uses_a_timer_instead_of_firing_each_frame(self):
        class Physics:
            speed = 1
            x = 0
            y = 0

            def check_collision(self, *args):
                return False

            def move(self, *args):
                return True

        class Entity:
            nome = "Runner"
            x = 0
            y = 0
            physics = Physics()

            def __init__(self):
                self.shots = 0

            def atirar(self, *args):
                self.shots += 1

        class Player:
            x = 4
            y = 0

        class Map:
            jogador = Player()

            def is_blocked_terrain(self, x, y):
                return False

        entity = Entity()
        ai = AIComponent(entity)
        ai.ranged_decision_timer = 0

        for _ in range(10):
            ai.update(Map(), 0.01)

        self.assertEqual(entity.shots, 1)


if __name__ == "__main__":
    unittest.main()
