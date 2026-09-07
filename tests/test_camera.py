import unittest

from core.camera import Camera


class CameraTests(unittest.TestCase):
    def test_following_uses_smoothing_after_initial_snap(self):
        camera = Camera()
        camera.update(40, 40, 1 / 60)
        old_x = camera.base_x

        camera.update(60, 40, 1 / 60)

        self.assertGreater(camera.base_x, old_x)
        self.assertLess(camera.base_x, (60.5) * 32 - 750)

    def test_trauma_decays_over_time(self):
        camera = Camera()
        camera.add_trauma(0.7)

        camera.update(40, 40, 0.1)
        remaining = camera.trauma
        camera.update(40, 40, 0.1)

        self.assertLess(camera.trauma, remaining)


if __name__ == "__main__":
    unittest.main()
