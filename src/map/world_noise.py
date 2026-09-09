from __future__ import annotations

from dataclasses import dataclass

from perlin_noise import PerlinNoise


@dataclass(frozen=True)
class NoiseScales:
    terrain: float = 40.0
    biome: float = 120.0
    desert: float = 72.0
    snow: float = 68.0
    detail: float = 26.0
    pond_edge: float = 18.0


class WorldNoise:
    """Agrupa campos de ruído e suas escalas sob uma única seed."""

    def __init__(self, seed: int, scales: NoiseScales | None = None):
        self.scales = scales or NoiseScales()
        self._terrain = PerlinNoise(octaves=1, seed=seed)
        self._biome = PerlinNoise(octaves=2, seed=seed + 1)
        self._desert = PerlinNoise(octaves=2, seed=seed + 2)
        self._snow = PerlinNoise(octaves=2, seed=seed + 3)
        self._detail = PerlinNoise(octaves=3, seed=seed + 4)
        self._pond_edge = PerlinNoise(octaves=2, seed=seed + 5)

    @staticmethod
    def _sample(noise, scale, x, y):
        return noise([x / scale, y / scale])

    def terrain(self, x, y):
        return self._sample(self._terrain, self.scales.terrain, x, y)

    def biome(self, x, y):
        return self._sample(self._biome, self.scales.biome, x, y)

    def desert(self, x, y):
        return self._sample(self._desert, self.scales.desert, x, y)

    def snow(self, x, y):
        return self._sample(self._snow, self.scales.snow, x, y)

    def detail(self, x, y):
        return self._sample(self._detail, self.scales.detail, x, y)

    def pond_edge(self, x, y):
        return self._sample(self._pond_edge, self.scales.pond_edge, x, y)
