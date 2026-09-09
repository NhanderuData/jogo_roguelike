from __future__ import annotations

import pygame

from core import config
from core.content import ContentCatalog
from core.audio import SoundManager
from core.context import GameContext
from core.input_manager import InputManager
from core.state_manager import Scene, StateManager
from graphics import recursos
from states.game_over_state import GameOverState
from states.game_state import GameState
from states.inventory_state import InventoryState
from states.menu_state import MenuState
from states.pause_state import PauseState


class GameApplication:
    """Pygame composition root and main loop."""

    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.LARGURA_TELA, config.ALTURA_TELA),
            pygame.FULLSCREEN | pygame.SCALED,
        )
        pygame.display.set_caption("Rogue Llama")
        self.clock = pygame.time.Clock()

        context = GameContext(
            input=InputManager(),
            content=ContentCatalog.load_default(),
            audio=SoundManager(),
        )
        self.context = context
        self.states = StateManager(context)
        self._register_scenes()

        recursos.carregar_tudo()
        recursos.validar_sprites_conteudo(context.content)
        self.states.change(Scene.MENU)

    def _register_scenes(self) -> None:
        self.states.register(Scene.MENU, MenuState)
        self.states.register(Scene.GAME, GameState)
        self.states.register(Scene.PAUSE, PauseState)
        self.states.register(Scene.INVENTORY, InventoryState)
        self.states.register(Scene.GAME_OVER, GameOverState)

    def run(self) -> None:
        try:
            while not self.context.quit_requested:
                dt = min(self.clock.tick(config.FPS) / 1000.0, 0.1)
                self.context.input.update()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.context.request_quit()
                        break
                    self.context.input.process_event(event)
                    self.states.handle_input(event)

                if self.context.quit_requested:
                    break

                self.states.update(dt)
                self.states.draw(self.screen)
                pygame.display.flip()
        finally:
            pygame.quit()
