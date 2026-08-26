from __future__ import annotations

from abc import ABC
from enum import Enum
from typing import Dict, List, Type

import pygame

from core.context import GameContext


class Scene(str, Enum):
    MENU = "menu"
    GAME = "game"
    PAUSE = "pause"
    INVENTORY = "inventory"
    GAME_OVER = "game_over"


class BaseState(ABC):
    """Contract shared by every screen and overlay in the game."""

    transparent = False

    def __init__(self, manager: "StateManager", context: GameContext):
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


class StateManager:
    """Owns scene navigation and draws transparent overlays correctly."""

    def __init__(self, context: GameContext):
        self.context = context
        self._stack: List[BaseState] = []
        self._routes: Dict[Scene, Type[BaseState]] = {}

    @property
    def stack(self) -> tuple[BaseState, ...]:
        return tuple(self._stack)

    @property
    def current(self) -> BaseState | None:
        return self._stack[-1] if self._stack else None

    def register(self, route: Scene, state_class: Type[BaseState]) -> None:
        self._routes[route] = state_class

    def _create(self, route: Scene) -> BaseState:
        try:
            state_class = self._routes[route]
        except KeyError as exc:
            raise ValueError(f"Scene route is not registered: {route.value}") from exc
        return state_class(self, self.context)

    def push(self, route: Scene, **kwargs) -> BaseState:
        state = self._create(route)
        state.enter(**kwargs)
        self._stack.append(state)
        return state

    def pop(self) -> BaseState | None:
        if not self._stack:
            return None
        state = self._stack.pop()
        state.exit()
        return state

    def change(self, route: Scene, **kwargs) -> BaseState:
        while self._stack:
            self.pop()
        return self.push(route, **kwargs)

    def handle_input(self, event: pygame.event.Event) -> None:
        if self.current:
            self.current.handle_input(event)

    def update(self, dt: float) -> None:
        if self.current:
            self.current.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        if not self._stack:
            return

        first_visible = len(self._stack) - 1
        while first_visible > 0 and self._stack[first_visible].transparent:
            first_visible -= 1

        for state in self._stack[first_visible:]:
            state.draw(surface)
