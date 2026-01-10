# src/efeitos.py
import pygame
from core import config

class TextoFlutuante:
    def __init__(self, x, y, texto, cor):
        self.x = x  # Posição no Grid
        self.y = y
        self.texto = str(texto)
        self.cor = cor
        self.vida = 60  # Dura 1 segundo
        self.offset_y = 0.0 # Começa no chão e sobe
        
        # Cria a fonte (Pequena e negrito)
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.image = self.font.render(self.texto, True, self.cor)
        self.shadow = self.font.render(self.texto, True, config.PRETO) # Sombra

    def update(self):
        self.vida -= 1
        self.offset_y -= 0.02 # Sobe devagarzinho

    def draw(self, surface, camera_x, camera_y):
        # Converte Grid -> Pixel
        screen_x = (self.x * config.TAMANHO_TILE) - camera_x + 10 
        screen_y = (self.y * config.TAMANHO_TILE) - camera_y + (self.offset_y * 32)
        
        # Desenha sombra deslocada e depois o texto
        surface.blit(self.shadow, (screen_x + 2, screen_y + 2))
        surface.blit(self.image, (screen_x, screen_y))