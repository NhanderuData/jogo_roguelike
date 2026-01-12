import pygame
from core import config
from core.input_manager import Actions

class InventoryState:
    def __init__(self, manager, registry, input_manager):
        self.manager = manager
        self.registry = registry # Precisamos acessar o registry para achar o Jogador se necessário
        self.input = input_manager
        
        # Pega a referência do jogador (passaremos via kwargs no enter)
        self.player = None
        
        self.font = pygame.font.SysFont("arial", 24)
        self.overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 200))

    def enter(self, **kwargs):
        # Recebe o objeto jogador quando entra no estado
        self.player = kwargs.get('player')

    def exit(self): pass

    def handle_input(self, event):
        self.input.process_event(event)

    def update(self, dt):
        if self.input.is_pressed(Actions.INVENTORY) or self.input.is_pressed(Actions.PAUSE):
            self.manager.pop()

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))
        
        title = self.font.render("INVENTÁRIO", True, config.AMARELO)
        surface.blit(title, (50, 50))
        
        if self.player and self.player.inventory:
            items = self.player.inventory.items
            y = 100
            if not items:
                txt = self.font.render("Vazio...", True, config.BRANCO)
                surface.blit(txt, (50, y))
            else:
                for i, item in enumerate(items):
                    txt = self.font.render(f"{i+1}. {item['name']} (x{item['qtd']})", True, config.BRANCO)
                    surface.blit(txt, (50, y))
                    y += 40