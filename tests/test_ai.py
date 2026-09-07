import unittest

from components.ai import AIComponent


class Entity:
    x = 0
    y = 0


class MapStub:
    largura = 8
    altura = 8

    def __init__(self, blocked):
        self.blocked = set(blocked)

    def is_blocked_terrain(self, x, y):
        return x < 0 or y < 0 or x >= self.largura or y >= self.altura or (x, y) in self.blocked


class NavigationTests(unittest.TestCase):
    def test_path_routes_around_blocked_tile(self):
        ai = AIComponent(Entity())
        map_obj = MapStub(blocked={(1, 0)})

        path = ai._find_path(map_obj, (2, 0))

        self.assertTrue(path)
        self.assertNotIn((1, 0), path)
        self.assertEqual(path[-1], (2, 0))


if __name__ == "__main__":
    unittest.main()
