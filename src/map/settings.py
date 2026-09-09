from __future__ import annotations

from dataclasses import dataclass
import math

from core import config


@dataclass(frozen=True)
class WorldSettings:
    """Configuração explícita do mundo, independente de globais no runtime."""

    width: int = config.LARGURA_MAPA
    height: int = config.ALTURA_MAPA
    chunk_size: int = config.TAMANHO_CHUNK
    enemy_count: int = 40

    @property
    def chunks_x(self) -> int:
        return math.ceil(self.width / self.chunk_size)

    @property
    def chunks_y(self) -> int:
        return math.ceil(self.height / self.chunk_size)

    def __post_init__(self) -> None:
        if self.width < 64 or self.height < 64:
            raise ValueError("World dimensions must be at least 64x64 tiles")
        if self.chunk_size <= 0:
            raise ValueError("Chunk size must be positive")
        if self.enemy_count < 0:
            raise ValueError("Enemy count cannot be negative")
