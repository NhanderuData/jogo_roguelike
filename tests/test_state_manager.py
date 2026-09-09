import unittest

import pygame

from core.content import ContentCatalog
from core.context import GameContext
from core.audio import NullSoundManager
from core.input_manager import InputManager
from core.state_manager import BaseState, Scene, StateManager


class StateManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.draws = []
        context = GameContext(InputManager(), ContentCatalog({}, {}))
        self.assertIsInstance(context.audio, NullSoundManager)
        self.manager = StateManager(context)

        draws = self.draws

        class WorldState(BaseState):
            def draw(self, surface):
                draws.append("world")

        class OverlayState(BaseState):
            transparent = True

            def draw(self, surface):
                draws.append("overlay")

        class MenuState(BaseState):
            def draw(self, surface):
                draws.append("menu")

        self.manager.register(Scene.GAME, WorldState)
        self.manager.register(Scene.PAUSE, OverlayState)
        self.manager.register(Scene.MENU, MenuState)

    def test_transparent_state_draws_over_previous_scene(self):
        self.manager.push(Scene.GAME)
        self.manager.push(Scene.PAUSE)

        self.manager.draw(pygame.Surface((8, 8)))

        self.assertEqual(self.draws, ["world", "overlay"])

    def test_opaque_state_hides_previous_scene(self):
        self.manager.push(Scene.GAME)
        self.manager.push(Scene.MENU)

        self.manager.draw(pygame.Surface((8, 8)))

        self.assertEqual(self.draws, ["menu"])

    def test_change_exits_the_old_stack(self):
        self.manager.push(Scene.GAME)
        current = self.manager.change(Scene.MENU)

        self.assertEqual(len(self.manager.stack), 1)
        self.assertIs(self.manager.current, current)

    def test_unregistered_route_has_clear_error(self):
        with self.assertRaisesRegex(ValueError, "not registered"):
            self.manager.push(Scene.INVENTORY)


if __name__ == "__main__":
    unittest.main()
