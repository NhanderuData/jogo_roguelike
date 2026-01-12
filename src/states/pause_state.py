import pygame
from core import config
from core.input_manager import Actions

class PauseState:
    def __init__(self, manager, registry, input_manager):
        self.manager = manager
        self.input_manager = input_manager
        
        # Cria um overlay semi-transparente
        self.overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 150)) # Preto com transparência
        
        self.font = pygame.font.SysFont("arial", 60, bold=True)
        self.txt_pause = self.font.render("PAUSADO", True, config.BRANCO)
        self.rect_pause = self.txt_pause.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2))

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def handle_input(self, event):
        self.input_manager.process_event(event)

    def update(self, dt):
        # Se apertar PAUSE novamente, sai do estado (pop) e volta ao jogo
        if self.input_manager.is_pressed(Actions.PAUSE):
            self.manager.pop()
            
        # Opção de Sair do Jogo pelo menu de pause
        if self.input_manager.is_pressed(Actions.QUIT):
            # Volta para o Menu Principal
            from states.menu_state import MenuState
            self.manager.change(MenuState)

    def draw(self, surface):
        # O StateManager já desenhou o jogo por baixo (graças à mudança na Parte 1)
        surface.blit(self.overlay, (0, 0))
        surface.blit(self.txt_pause, self.rect_pause)