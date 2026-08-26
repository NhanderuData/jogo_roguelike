import pygame
from core import config
from core.input_manager import Actions 
from core.state_manager import BaseState, Scene

class GameOverState(BaseState):
    def __init__(self, manager, context):
        super().__init__(manager, context)
        
        self.font_big = pygame.font.SysFont("arial", 64, bold=True)
        self.font_small = pygame.font.SysFont("arial", 24)
        
        self.txt_titulo = self.font_big.render("GAME OVER", True, (200, 0, 0))
        self.txt_instr = self.font_small.render("Pressione R para Reiniciar", True, config.BRANCO)
        
        self.rect_titulo = self.txt_titulo.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2 - 50))
        self.rect_instr = self.txt_instr.get_rect(center=(config.LARGURA_TELA//2, config.ALTURA_TELA//2 + 20))

    def enter(self, **kwargs):
        pass

    def exit(self):
        pass

    def update(self, dt):
        # Verifica se a ação RESTART (Tecla R) foi ativada neste frame
        if self.input.is_pressed(Actions.RESTART):
            self.manager.change(Scene.GAME)

    def draw(self, surface):
        surface.fill((20, 0, 0))
        surface.blit(self.txt_titulo, self.rect_titulo)
        surface.blit(self.txt_instr, self.rect_instr)
