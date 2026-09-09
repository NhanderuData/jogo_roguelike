import pygame
from core import config
from graphics import recursos

class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 32, bold=True)
        self._icon_cache = {}

    def _scaled_icon(self, key, size):
        cache_key = (key, size)
        icon = self._icon_cache.get(cache_key)
        if icon is None:
            source = recursos.SPRITES.get(key)
            if source:
                icon = pygame.transform.scale(source, size)
                self._icon_cache[cache_key] = icon
        return icon

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
        # O papel da entidade define se ela possui status de sobrevivência.
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
                surface.blit(txt_bleed, (20, 140))

            if jogador.status.energy_remaining > 0:
                self.desenhar_barra(
                    surface, 20, 112,
                    jogador.status.energy_remaining, 8.0,
                    (15, 45, 70), (60, 190, 255),
                    largura=150, altura=10,
                )

        if jogador.combat.armor > 0:
            self.desenhar_barra(
                surface, 180, 70,
                jogador.combat.armor, jogador.combat.max_armor,
                (35, 40, 30), (135, 150, 105),
                largura=130, altura=15,
                texto_label="ARMOR",
            )

        if hasattr(jogador, "weapons") and jogador.weapons:
            self._draw_weapons(surface, jogador)

    def _draw_weapons(self, surface, jogador):
        weapons = jogador.weapons
        slot_size = 64
        gap = 8
        total_width = (
            len(weapons.slot_order) * slot_size
            + max(0, len(weapons.slot_order) - 1) * gap
        )
        start_x = config.LARGURA_TELA - total_width - 20
        y = config.ALTURA_TELA - slot_size - 20

        for index, weapon_id in enumerate(weapons.slot_order):
            x = start_x + index * (slot_size + gap)
            unlocked = weapon_id in weapons.unlocked
            selected = weapon_id == weapons.current_id
            background = (24, 27, 30) if unlocked else (12, 13, 14)
            border = (255, 210, 70) if selected else (90, 95, 100)
            pygame.draw.rect(surface, background, (x, y, slot_size, slot_size))
            pygame.draw.rect(surface, border, (x, y, slot_size, slot_size), 3 if selected else 1)

            definition = weapons.content.weapons[weapon_id]
            icon = self._scaled_icon(definition.sprite, (56, 56))
            if icon and unlocked:
                surface.blit(icon, (x + 4, y + 4))
            elif not unlocked:
                pygame.draw.line(surface, (55, 58, 60), (x + 18, y + 18), (x + 46, y + 46), 3)
                pygame.draw.line(surface, (55, 58, 60), (x + 46, y + 18), (x + 18, y + 46), 3)

        weapon = weapons.current
        name = self.font.render(weapon.name, True, config.BRANCO)
        surface.blit(name, (start_x, y - 26))

        if weapon.kind == "ranged":
            magazine = weapons.magazines[weapons.current_id]
            reserve = jogador.inventory.ammo_count(weapon.ammo_type)
            color = (230, 70, 60) if magazine == 0 else config.BRANCO
            ammo = self.font_huge.render(f"{magazine} / {reserve}", True, color)
            ammo_rect = ammo.get_rect(bottomright=(config.LARGURA_TELA - 20, y - 5))
            surface.blit(ammo, ammo_rect)

        if weapons.is_reloading:
            width = total_width
            pygame.draw.rect(surface, (35, 35, 35), (start_x, y - 8, width, 4))
            pygame.draw.rect(
                surface,
                (240, 190, 70),
                (start_x, y - 8, int(width * weapons.reload_progress), 4),
            )
