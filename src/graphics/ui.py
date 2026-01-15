# src/graphics/ui.py
import pygame
from core import config

class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)

    def desenhar_barra(self, surface, x, y, atual, maximo, cor_fundo, cor_cheia, largura=200, altura=20, texto_label=""):
        if maximo <= 0: maximo = 1
        pct = max(0, min(1, atual / maximo))
        
        pygame.draw.rect(surface, cor_fundo, (x, y, largura, altura))
        largura_atual = int(largura * pct)
        if largura_atual > 0:
            pygame.draw.rect(surface, cor_cheia, (x, y, largura_atual, altura))
        pygame.draw.rect(surface, config.BRANCO, (x, y, largura, altura), 2)

        if texto_label:
            # Sombra do texto para leitura melhor
            txt_surf = self.font.render(f"{texto_label}", True, config.BRANCO)
            surface.blit(txt_surf, (x + 5, y + 2))

    def draw(self, surface, jogador):
        if not jogador: return

        # 1. VIDA (Vermelho)
        self.desenhar_barra(surface, 20, 20, jogador.hp, jogador.hp_max, 
                            (50, 0, 0), (200, 0, 0), texto_label=f"HP {int(jogador.hp)}")

        # 2. FOME (Laranja/Amarelo Queimado) - NOVO
        # Fica abaixo da vida
        self.desenhar_barra(surface, 20, 45, jogador.combat.fome, jogador.combat.max_fome, 
                            (50, 30, 0), (200, 120, 0), largura=150, altura=15, 
                            texto_label=f"FOME {int(jogador.combat.fome)}%")

        # 3. MUNIÇÃO (Amarelo) - Útil para shooter de zumbi
        if jogador.inventory:
            txt_ammo = self.font_big.render(f"Munição: {jogador.inventory.municao}", True, config.AMARELO)
            surface.blit(txt_ammo, (20, config.ALTURA_TELA - 50))

        # Nível (canto superior direito da UI)
        txt_lvl = self.font_big.render(f"Dia 1 - Lvl {jogador.nivel}", True, config.BRANCO)
        surface.blit(txt_lvl, (20, 70))