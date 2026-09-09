import unittest

import pygame

from components.ai import AIComponent
from components.sprite import SpriteComponent
from graphics import recursos


class TimingTests(unittest.TestCase):
    def test_directional_sprite_switches_state_and_direction(self):
        idle_down = pygame.Surface((2, 2))
        move_left = pygame.Surface((2, 2))
        move_right = pygame.Surface((2, 2))
        recursos.SPRITES["direction_test"] = {
            "idle": {"down": [idle_down]},
            "move": {"left": [move_left], "right": [move_right]},
        }

        class Entity:
            moving = False

        entity = Entity()
        sprite = SpriteComponent(entity, "direction_test")
        sprite.update(0.0)
        self.assertIs(sprite.image, idle_down)

        entity.moving = True
        sprite.set_direction(-1, 0)
        sprite.update(0.0)
        self.assertIs(sprite.image, move_left)

        # Os inimigos do pacote têm vista lateral. Ao andar para cima, eles
        # mantêm o último lado horizontal em vez de virarem para a direita.
        sprite.set_direction(0, -1)
        sprite.update(0.0)
        self.assertIs(sprite.image, move_left)
        recursos.SPRITES.pop("direction_test", None)

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
            x = 0
            y = 0
            physics = Physics()
            ai_mode = "hybrid"
            ranged_interval = 1.25

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
