import unittest

import pygame

from map.spatial_hash import SpatialHash


class Entity:
    def __init__(self, rect):
        self.hitbox = pygame.Rect(rect)
        self.hp = 10


class SpatialHashTests(unittest.TestCase):
    def test_query_returns_only_nearby_entities(self):
        nearby = Entity((10, 10, 16, 16))
        distant = Entity((500, 500, 16, 16))
        index = SpatialHash(cell_tiles=2)
        index.rebuild([nearby, distant])

        result = index.query(pygame.Rect(0, 0, 32, 32))

        self.assertEqual(result, [nearby])

    def test_query_preserves_insertion_order(self):
        first = Entity((10, 10, 16, 16))
        second = Entity((12, 12, 16, 16))
        index = SpatialHash(cell_tiles=2)
        index.insert(first)
        index.insert(second)

        result = index.query(pygame.Rect(0, 0, 32, 32))

        self.assertEqual(result, [first, second])

    def test_update_moves_entity_between_cells(self):
        entity = Entity((10, 10, 16, 16))
        index = SpatialHash(cell_tiles=2)
        index.insert(entity)
        entity.hitbox.topleft = (300, 300)

        index.update(entity)

        self.assertNotIn(entity, index.query(pygame.Rect(0, 0, 32, 32)))
        self.assertIn(entity, index.query(pygame.Rect(288, 288, 64, 64)))


if __name__ == "__main__":
    unittest.main()
