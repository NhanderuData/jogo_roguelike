import pygame
from core import config

class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 32, bold=True)

    def desenhar_barra(self, surface, x, y, atual, maximo, cor_fundo, cor_cheia, largura=200, altura=20, texto_label=""):
        if maximo <= 0: maximo = 1
        pct = max(0, min(1, atual / maximo))
        
        # 1. Fundo
        pygame.draw.rect(surface, cor_fundo, (x, y, largura, altura))
        # 2. Parte Cheia
        largura_atual = int(largura * pct)
        if largura_atual > 0:
            pygame.draw.rect(surface, cor_cheia, (x, y, largura_atual, altura))
        # 3. Borda
        pygame.draw.rect(surface, config.BRANCO, (x, y, largura, altura), 2)
        # 4. Texto
        if texto_label:
            txt_surf = self.font.render(f"{texto_label} {int(atual)}/{int(maximo)}", True, config.BRANCO)
            txt_rect = txt_surf.get_rect(center=(x + largura/2, y + altura/2))
            surface.blit(txt_surf, txt_rect)

    def draw(self, surface, jogador):
        if not jogador: return

        # 1. Barra de Vida (HP) - Vermelha (Y=20)
        self.desenhar_barra(
            surface, 20, 20, 
            jogador.hp, jogador.hp_max, 
            (50, 0, 0), (200, 0, 0), 
            texto_label="HP"
        )

        # 2. Barra de XP - Amarela (Y=50)
        self.desenhar_barra(
            surface, 20, 50, 
            jogador.xp, jogador.xp_proximo_nivel, 
            (50, 50, 0), (255, 215, 0), 
            largura=150, altura=10
        )
        
        # 3. Nível
        txt_lvl = self.font_big.render(f"Lvl {jogador.nivel}", True, config.BRANCO)
        surface.blit(txt_lvl, (240, 20))

        # --- 4. SISTEMA DE SOBREVIVÊNCIA (NOVO) ---
        # Verifica se o jogador possui o componente de Status (apenas o Survivor tem)
        if hasattr(jogador, 'status') and jogador.status:
            
            # FOME (Laranja) - Y=70
            self.desenhar_barra(
                surface, 20, 70,
                jogador.status.fome, jogador.status.max_fome,
                (100, 50, 0), (255, 140, 0), 
                largura=150, altura=15,
                texto_label="FOME"
            )

            # SEDE (Azul) - Y=90 (Logo abaixo da fome)
            self.desenhar_barra(
                surface, 20, 90,
                jogador.status.sede, jogador.status.max_sede,
                (0, 0, 100), (50, 100, 255), 
                largura=150, altura=15,
                texto_label="SEDE"
            )

            # AVISO DE SANGRAMENTO - Y=120
            if jogador.status.sangramento > 0:
                txt_bleed = self.font_big.render("SANGRANDO!", True, (255, 0, 0))
                surface.blit(txt_bleed, (20, 120))

        # 5. Munição (Canto Inferior)
        if hasattr(jogador, 'inventory') and jogador.inventory:
            qtd_balas = jogador.inventory.municao
            
            cor_ammo = config.BRANCO
            if qtd_balas == 0: cor_ammo = (200, 50, 50)
            elif qtd_balas < 10: cor_ammo = (255, 255, 0)
            
            surf_ammo = self.font_huge.render(f"{qtd_balas}", True, cor_ammo)
            rect_ammo = surf_ammo.get_rect(bottomright=(config.LARGURA_TELA - 20, config.ALTURA_TELA - 20))
            
            surf_label = self.font.render("AMMO", True, config.CINZA_CLARO)
            rect_label = surf_label.get_rect(bottomright=(config.LARGURA_TELA - 20, rect_ammo.top - 5))
            
            surface.blit(surf_label, rect_label)
            surface.blit(surf_ammo, rect_ammo)