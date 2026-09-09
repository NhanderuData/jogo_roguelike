from __future__ import annotations


class RoadGenerator:
    """Gera estradas e converte travessias de água em pontes."""

    def __init__(self, world, rng, settings):
        self.world = world
        self.rng = rng
        self.settings = settings

    def generate(self) -> None:
        chunk_size = self.settings.chunk_size
        chunks_x = self.settings.chunks_x
        chunks_y = self.settings.chunks_y
        connections = []
        visited = []

        cx, cy = 0, self.rng.randint(0, chunks_y - 1)
        visited.append((cx, cy))
        while cx < chunks_x - 1:
            options = [(1, 0), (1, 0), (1, 0)]
            if cy > 0:
                options.append((0, -1))
            if cy + 1 < chunks_y:
                options.append((0, 1))
            dx, dy = self.rng.choice(options)
            next_cell = cx + dx, cy + dy
            connections.append(((cx, cy), next_cell))
            visited.append(next_cell)
            cx, cy = next_cell

        for _ in range(3):
            if not visited:
                break
            bx, by = self.rng.choice(visited)
            for _ in range(self.rng.randint(1, 3)):
                dx, dy = self.rng.choice(((0, 1), (0, -1), (1, 0), (-1, 0)))
                nx, ny = bx + dx, by + dy
                if 0 <= nx < chunks_x and 0 <= ny < chunks_y:
                    connections.append(((bx, by), (nx, ny)))
                    visited.append((nx, ny))
                    bx, by = nx, ny

        for first, second in connections:
            x1 = first[0] * chunk_size + chunk_size // 2
            y1 = first[1] * chunk_size + chunk_size // 2
            x2 = second[0] * chunk_size + chunk_size // 2
            y2 = second[1] * chunk_size + chunk_size // 2
            self._draw_strip(x1, y1, x2, y2)

    def _draw_strip(self, x1, y1, x2, y2, width=3) -> None:
        orientation = "horizontal" if abs(x2 - x1) >= abs(y2 - y1) else "vertical"
        radius = width // 2
        for y in range(min(y1, y2) - radius, max(y1, y2) + radius + 1):
            for x in range(min(x1, x2) - radius, max(x1, x2) + radius + 1):
                tile = self.world.obter_tile(x, y)
                if not tile:
                    continue
                over_water = tile.tipo == "deep_water"
                tile.tipo = "bridge" if over_water else "estrada"
                tile.bloqueado = False
                tile.decoracao = None
                tile.bioma = "ponte" if over_water else "estrada"
                tile.orientacao = orientation if over_water else None
                self._remove_entities_at(x, y)

    def _remove_entities_at(self, x, y) -> None:
        for entity in tuple(self.world.entidades):
            if int(entity.x) == x and int(entity.y) == y:
                self.world.entidades.remove(entity)
                self.world._tree_positions.discard((x, y))
