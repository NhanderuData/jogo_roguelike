from __future__ import annotations

from abc import ABC
from typing import Any, Protocol

import pygame

from core.context import GameContext

class StateManagerProtocol(Protocol):
    def push(self, route: Any, **kwargs): ...
    def pop(self): ...
    def change(self, route: Any, **kwargs): ...


class BaseState(ABC):
    """Contrato de ciclo de vida compartilhado por cenas e overlays."""

    transparent = False

    def __init__(self, manager: StateManagerProtocol, context: GameContext):
        self.manager = manager
        self.context = context
        self.input = context.input

    def enter(self, **kwargs) -> None:
        pass

    def exit(self) -> None:
        pass

    def handle_input(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass
