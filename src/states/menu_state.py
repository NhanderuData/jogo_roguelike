import pygame
import math
from core import config
from core.input_manager import Actions
from core.state_manager import Scene
from states.base_state import BaseState

class MenuState(BaseState):
    def __init__(self, manager, context):
        super().__init__(manager, context)
        
        # Fontes
        self.font_title = pygame.font.SysFont("arial", 80, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)
        
        # Textos
        self.txt_titulo = self.font_title.render("ROGUE LLAMA", True, config.BRANCO)
        self.txt_start = self.font_small.render("Pressione ENTER para Jogar", True, (200, 200, 200))
        self.txt_quit = self.font_small.render("ESC para Sair", True, (150, 50, 50))
        
        # Centralização
        self.rect_titulo = self.txt_titulo.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2 - 60))
        self.rect_start = self.txt_start.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2 + 40))
        self.rect_quit = self.txt_quit.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2 + 80))
        
        # Efeito de piscar
        self.timer = 0

    def enter(self, **kwargs):
        # Toca música de abertura se tiver
        pass

    def exit(self):
        pass

    def update(self, dt):
        self.timer += dt
        
        # Detecta ENTER para começar o jogo
        # Vamos precisar adicionar a ação START no InputManager depois!
        if self.input.is_pressed(Actions.START):
            self.manager.change(Scene.GAME)
            
        # Detecta QUIT para fechar
        if self.input.is_pressed(Actions.QUIT):
            self.context.request_quit()

    def draw(self, surface):
        # Fundo roxo escuro (estilo místico)
        surface.fill((30, 0, 40))
        
        # Desenha Título
        # Um leve efeito de sombra
        shadow = self.font_title.render("ROGUE LLAMA", True, (0, 0, 0))
        surface.blit(shadow, (self.rect_titulo.x + 4, self.rect_titulo.y + 4))
        surface.blit(self.txt_titulo, self.rect_titulo)
        
        # Texto piscando
        if math.sin(self.timer * 5) > -0.5: # Pisca rápido
            surface.blit(self.txt_start, self.rect_start)
            
        surface.blit(self.txt_quit, self.rect_quit)
