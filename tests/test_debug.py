import unittest

from debug import _BLOCKED_TILE_OVERLAYS, _blocked_tile_overlay


class DebugOverlayTests(unittest.TestCase):
    def setUp(self):
        _BLOCKED_TILE_OVERLAYS.clear()

    def test_blocked_tile_overlay_is_reused(self):
        first = _blocked_tile_overlay(32)
        second = _blocked_tile_overlay(32)

        self.assertIs(first, second)
        self.assertEqual(first.get_size(), (32, 32))
        self.assertEqual(first.get_at((0, 0)), (255, 0, 0, 100))


if __name__ == "__main__":
    unittest.main()
