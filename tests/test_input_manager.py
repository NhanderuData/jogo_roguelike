import unittest
import pygame

from core.input_manager import Actions, InputManager
from core.audio import NullSoundManager, SoundManager
from graphics.ui import UI


class InputManagerTests(unittest.TestCase):
    def test_f3_toggles_debug_action(self):
        inputs = InputManager()
        inputs.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F3))
        self.assertTrue(inputs.is_pressed(Actions.TOGGLE_DEBUG))

    def test_m_toggles_mute_action(self):
        inputs = InputManager()
        inputs.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m))
        self.assertTrue(inputs.is_pressed(Actions.TOGGLE_MUTE))

    def test_mouse_wheel_scroll_tracking(self):
        inputs = InputManager()
        inputs.process_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1))
        self.assertEqual(inputs.get_mouse_wheel(), 1)

        inputs.update()
        self.assertEqual(inputs.get_mouse_wheel(), 0)

    def test_middle_click_triggers_reset_zoom_action(self):
        inputs = InputManager()
        inputs.process_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=2))
        self.assertTrue(inputs.is_pressed(Actions.RESET_ZOOM))


class AudioMuteTests(unittest.TestCase):
    def test_null_sound_manager_toggle_mute(self):
        audio = NullSoundManager()
        self.assertFalse(audio.muted)
        audio.toggle_mute()
        self.assertTrue(audio.muted)
        audio.toggle_mute()
        self.assertFalse(audio.muted)

    def test_sound_manager_mute_controls(self):
        audio = SoundManager()
        self.assertFalse(audio.muted)
        audio.toggle_mute()
        self.assertTrue(audio.muted)
        audio.set_muted(False)
        self.assertFalse(audio.muted)

    def test_ui_mute_button_rect_and_click_detection(self):
        rect = UI.get_mute_button_rect()
        self.assertIsInstance(rect, pygame.Rect)
        self.assertTrue(rect.width > 0 and rect.height > 0)
        self.assertTrue(rect.collidepoint(rect.centerx, rect.centery))


if __name__ == "__main__":
    unittest.main()
