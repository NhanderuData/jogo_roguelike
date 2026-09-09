import pygame
from core import config
from core.input_manager import Actions
from states.base_state import BaseState
from graphics import recursos

class InventoryState(BaseState):
    transparent = True

    def __init__(self, manager, context):
        super().__init__(manager, context)
        
        self.player = None
        
        # --- NOVO: Índice de Seleção ---
        self.selected_index = 0
        
        self.font = pygame.font.SysFont("arial", 24)
        self.font_selected = pygame.font.SysFont("arial", 24, bold=True) # Fonte para o item selecionado
        
        self.overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 200))
        self._icon_cache = {}

    def enter(self, **kwargs):
        self.player = kwargs.get('player')
        # Resetar a seleção ao abrir
        self.selected_index = 0

    def exit(self): 
        pass

    def update(self, dt):
        # 1. Fechar Inventário
        if self.input.is_pressed(Actions.INVENTORY) or self.input.is_pressed(Actions.PAUSE):
            self.manager.pop()
            return

        if not self.player or not self.player.inventory:
            return

        items = self.player.inventory.items
        qtd_items = len(items)

        # 2. Navegação (Cima / Baixo)
        if self.input.is_pressed(Actions.MOVE_DOWN):
            self.selected_index += 1
            if self.selected_index >= qtd_items:
                self.selected_index = 0 # Volta ao topo
                
        if self.input.is_pressed(Actions.MOVE_UP):
            self.selected_index -= 1
            if self.selected_index < 0:
                self.selected_index = qtd_items - 1 # Vai para o fundo

        # 3. Usar Item (Enter / Start)
        if self.input.is_pressed(Actions.START) and qtd_items > 0:
            # Chama a função lógica que já criaste no componente de inventário
            sucesso = self.player.inventory.usar_item(self.selected_index, self.player)
            
            if sucesso:
                # Se o item foi gasto, ajustamos o índice para não ficar fora da lista
                if self.selected_index >= len(self.player.inventory.items):
                    self.selected_index = max(0, len(self.player.inventory.items) - 1)

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))
        
        title = self.font.render("INVENTÁRIO", True, config.AMARELO)
        surface.blit(title, (50, 50))
        
        if self.player and self.player.inventory:
            items = self.player.inventory.items
            
            if not items:
                txt = self.font.render("Vazio...", True, config.BRANCO)
                surface.blit(txt, (50, 100))
            else:
                y = 100
                for i, item in enumerate(items):
                    nome = item['name']
                    qtd = item['qtd']
                    
                    # --- Lógica Visual de Seleção ---
                    if i == self.selected_index:
                        texto_str = f"> {nome} (x{qtd}) <"
                        cor = config.AMARELO
                        font_to_use = self.font_selected
                    else:
                        texto_str = f"  {nome} (x{qtd})"
                        cor = config.BRANCO
                        font_to_use = self.font
                    
                    txt = font_to_use.render(texto_str, True, cor)
                    definition = self.context.content.items.get(nome)
                    sprite_key = definition.sprite if definition else None
                    icon = self._icon_cache.get(sprite_key)
                    if sprite_key and icon is None:
                        source = recursos.SPRITES.get(sprite_key)
                        if source:
                            icon = pygame.transform.scale(source, (36, 36))
                            self._icon_cache[sprite_key] = icon
                    if icon:
                        surface.blit(icon, (50, y - 6))
                    surface.blit(txt, (96, y))
                    y += 44
                    
        # Desenha Stats do Jogador para referência
        if self.player:
             stats = f"HP: {self.player.hp}/{self.player.hp_max}"
             txt_stats = self.font.render(stats, True, (255, 100, 100))
             surface.blit(txt_stats, (500, 50))
