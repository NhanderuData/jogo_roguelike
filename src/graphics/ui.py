# src/ui.py
import pygame
from graphics import config

class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True) # Fonte padrão do sistema
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)

    def desenhar_barra(self, surface, x, y, atual, maximo, cor_fundo, cor_cheia, largura=200, altura=20, texto_label=""):
        if maximo <= 0: maximo = 1
        pct = max(0, min(1, atual / maximo))
        
        # 1. Fundo (Escuro)
        pygame.draw.rect(surface, cor_fundo, (x, y, largura, altura))
        
        # 2. Parte Cheia (Colorida)
        largura_atual = int(largura * pct)
        if largura_atual > 0:
            pygame.draw.rect(surface, cor_cheia, (x, y, largura_atual, altura))
            
        # 3. Borda (Branca/Preta)
        pygame.draw.rect(surface, config.BRANCO, (x, y, largura, altura), 2)

        # 4. Texto (Opcional)
        if texto_label:
            txt_surf = self.font.render(f"{texto_label} {int(atual)}/{int(maximo)}", True, config.BRANCO)
            # Centraliza o texto na barra
            txt_rect = txt_surf.get_rect(center=(x + largura/2, y + altura/2))
            surface.blit(txt_surf, txt_rect)

    def draw(self, surface, jogador):
        if not jogador: return

        # --- BARRA DE VIDA (Vermelha) ---
        self.desenhar_barra(
            surface, 
            x=20, y=20, 
            atual=jogador.hp, 
            maximo=jogador.hp_max, 
            cor_fundo=(50, 0, 0), 
            cor_cheia=(200, 0, 0),
            texto_label="HP"
        )

        # --- BARRA DE XP (Azul ou Dourada) ---
        # Fica logo abaixo da vida
        self.desenhar_barra(
            surface, 
            x=20, y=50, 
            atual=jogador.xp, 
            maximo=jogador.xp_proximo_nivel, 
            cor_fundo=(50, 50, 0), 
            cor_cheia=(255, 215, 0), # Dourado
            largura=150, altura=10, # Mais fina
            texto_label=""
        )
        
        # --- TEXTO DE NÍVEL ---
        txt_lvl = self.font_big.render(f"Lvl {jogador.nivel}", True, config.BRANCO)
        surface.blit(txt_lvl, (20 + 210, 20)) # Ao lado da barra de vida