import unittest

import pygame

from core.input_manager import Actions, InputManager


class InputManagerTests(unittest.TestCase):
    def test_f3_toggles_debug_action(self):
        inputs = InputManager()

        inputs.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))

        self.assertTrue(inputs.is_pressed(Actions.TOGGLE_DEBUG))


if __name__ == "__main__":
    unittest.main()
