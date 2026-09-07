from __future__ import annotations

from collections import defaultdict

import pygame

from core import config


class SpatialHash:
    """Indice espacial simples para entidades com hitboxes em pixels."""

    def __init__(self, cell_tiles: int = 4):
        self.cell_size = cell_tiles * config.TAMANHO_TILE
        self._cells = defaultdict(set)
        self._entity_cells = {}

    def clear(self):
        self._cells.clear()
        self._entity_cells.clear()

    def rebuild(self, entities):
        self.clear()
        for entity in entities:
            if getattr(entity, "hp", 0) > 0:
                self.insert(entity)

    def _keys_for_rect(self, rect: pygame.Rect):
        left = rect.left // self.cell_size
        right = (rect.right - 1) // self.cell_size
        top = rect.top // self.cell_size
        bottom = (rect.bottom - 1) // self.cell_size
        return {
            (cx, cy)
            for cy in range(top, bottom + 1)
            for cx in range(left, right + 1)
        }

    def insert(self, entity):
        keys = self._keys_for_rect(entity.hitbox)
        self._entity_cells[entity] = keys
        for key in keys:
            self._cells[key].add(entity)

    def remove(self, entity):
        for key in self._entity_cells.pop(entity, ()):
            cell = self._cells.get(key)
            if cell is None:
                continue
            cell.discard(entity)
            if not cell:
                del self._cells[key]

    def update(self, entity):
        new_keys = self._keys_for_rect(entity.hitbox)
        old_keys = self._entity_cells.get(entity, set())
        if new_keys == old_keys:
            return
        for key in old_keys - new_keys:
            self._cells[key].discard(entity)
            if not self._cells[key]:
                del self._cells[key]
        for key in new_keys - old_keys:
            self._cells[key].add(entity)
        self._entity_cells[entity] = new_keys

    def query(self, rect: pygame.Rect):
        result = set()
        for key in self._keys_for_rect(rect):
            result.update(self._cells.get(key, ()))
        return result
