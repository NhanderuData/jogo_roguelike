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

    def test_camera_zoom_expands_viewport(self):
        camera = Camera()
        self.assertEqual(camera.get_view_width(), 1500)
        self.assertEqual(camera.get_view_height(), 920)

        # Ao afastar a câmera (zoom 0.5x), o viewport expande para o dobro do tamanho
        camera.set_target_zoom(0.5)
        camera.zoom = 0.5
        self.assertEqual(camera.get_view_width(), 3000)
        self.assertEqual(camera.get_view_height(), 1840)

    def test_camera_zoom_clamps_limits(self):
        camera = Camera()
        camera.set_target_zoom(0.01)
        self.assertEqual(camera.target_zoom, camera.min_zoom)

        camera.set_target_zoom(99.0)
        self.assertEqual(camera.target_zoom, camera.max_zoom)

    def test_screen_to_world_conversion_with_zoom(self):
        camera = Camera()
        camera.camera_x = 320.0
        camera.camera_y = 640.0
        camera.zoom = 1.0

        # Sem zoom: (camera_x + screen_x) / 32
        self.assertEqual(camera.screen_to_world_x(32.0), (320.0 + 32.0) / 32.0)

        # Com zoom 0.5x: o ponto na tela representa o dobro da distância em pixels no mundo
        camera.zoom = 0.5
        self.assertEqual(camera.screen_to_world_x(32.0), (320.0 + 64.0) / 32.0)


if __name__ == "__main__":
    unittest.main()
