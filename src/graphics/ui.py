import pygame
from core import config
from graphics import recursos

class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.font_big = pygame.font.SysFont("arial", 24, bold=True)
        self.font_huge = pygame.font.SysFont("arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("arial", 10, bold=True)
        self._icon_cache = {}
        self.banner_text = ""
        self.banner_color = (255, 255, 255)
        self.banner_timer = 0.0
        self.banner_duration = 3.5

    def show_banner(self, text, color=(255, 255, 255), duration=3.5):
        self.banner_text = text
        self.banner_color = color
        self.banner_timer = duration
        self.banner_duration = duration

    def update(self, dt):
        if self.banner_timer > 0:
            self.banner_timer = max(0.0, self.banner_timer - dt)

    @staticmethod
    def get_mute_button_rect():
        return pygame.Rect(config.LARGURA_TELA - 64, 16, 44, 40)

    def desenhar_botao_mute(self, surface, audio, mouse_pos):
        btn_rect = self.get_mute_button_rect()
        is_hovered = btn_rect.collidepoint(mouse_pos)
        is_muted = getattr(audio, "muted", False)

        bg_color = (40, 46, 54) if is_hovered else (20, 24, 28)
        border_color = (255, 215, 70) if is_hovered else (75, 85, 95)
        if is_muted:
            border_color = (220, 70, 70) if not is_hovered else (255, 100, 100)

        pygame.draw.rect(surface, bg_color, btn_rect, border_radius=6)
        pygame.draw.rect(surface, border_color, btn_rect, 2, border_radius=6)

        cx = btn_rect.centerx
        cy = btn_rect.centery - 4

        speaker_color = (230, 235, 240) if not is_muted else (170, 175, 180)

        # Corpo do alto-falante
        pygame.draw.rect(surface, speaker_color, (cx - 10, cy - 4, 5, 8))
        pygame.draw.polygon(
            surface,
            speaker_color,
            [(cx - 6, cy - 4), (cx + 1, cy - 9), (cx + 1, cy + 9), (cx - 6, cy + 4)],
        )

        if not is_muted:
            wave_color = (120, 200, 255) if is_hovered else (220, 235, 250)
            pygame.draw.arc(surface, wave_color, (cx - 2, cy - 6, 8, 12), -1.1, 1.1, 2)
            pygame.draw.arc(surface, wave_color, (cx + 1, cy - 10, 12, 20), -1.1, 1.1, 2)
        else:
            pygame.draw.line(surface, (235, 60, 60), (cx - 9, cy + 9), (cx + 10, cy - 9), 3)

        txt_m = self.font_small.render("[M]", True, (160, 170, 180) if not is_hovered else config.BRANCO)
        surface.blit(txt_m, (cx - txt_m.get_width() // 2, btn_rect.bottom - 13))

    def desenhar_relogio_e_tempo(self, surface, time_system):
        if not time_system:
            return

        x = config.LARGURA_TELA - 235
        y = 16
        w = 160
        h = 40

        bg_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, (18, 22, 28), bg_rect, border_radius=6)

        phase_colors = {
            "Dia": (255, 215, 70),
            "Entardecer": (255, 130, 45),
            "Noite": (120, 160, 245),
            "Amanhecer": (255, 175, 80),
        }
        border_color = phase_colors.get(time_system.phase_label, (180, 180, 180))
        pygame.draw.rect(surface, border_color, bg_rect, 2, border_radius=6)

        icon_cx = x + 20
        icon_cy = y + h // 2
        if time_system.is_night:
            pygame.draw.circle(surface, (210, 230, 255), (icon_cx, icon_cy), 8)
            pygame.draw.circle(surface, (18, 22, 28), (icon_cx + 4, icon_cy - 2), 6)
        else:
            pygame.draw.circle(surface, border_color, (icon_cx, icon_cy), 7)
            pygame.draw.circle(surface, (255, 245, 180), (icon_cx, icon_cy), 4)

        txt_str = f"Dia {time_system.day_count} • {time_system.phase_label}"
        txt = self.font.render(txt_str, True, config.BRANCO)
        surface.blit(txt, (x + 36, y + 10))

    def desenhar_banner(self, surface):
        if self.banner_timer <= 0 or not self.banner_text:
            return

        alpha_factor = min(1.0, self.banner_timer / 0.6)
        alpha = int(255 * alpha_factor)

        txt = self.font_big.render(self.banner_text, True, self.banner_color)
        padding_x = 24
        padding_y = 12
        bw = txt.get_width() + padding_x * 2
        bh = txt.get_height() + padding_y * 2
        bx = (config.LARGURA_TELA - bw) // 2
        by = 80

        banner_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        banner_surf.fill((15, 18, 24, int(220 * alpha_factor)))
        border_c = (*self.banner_color[:3], alpha)
        pygame.draw.rect(banner_surf, border_c, (0, 0, bw, bh), 2, border_radius=8)

        txt_alpha = txt.copy()
        txt_alpha.set_alpha(alpha)
        banner_surf.blit(txt_alpha, (padding_x, padding_y))

        surface.blit(banner_surf, (bx, by))

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

    def draw(self, surface, jogador, audio=None, mouse_pos=(0, 0), time_system=None):
        if audio is not None:
            self.desenhar_botao_mute(surface, audio, mouse_pos)

        if time_system is not None:
            self.desenhar_relogio_e_tempo(surface, time_system)

        self.desenhar_banner(surface)

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

            # AVISO DE SANGRAMENTO - Y=135
            bleed_y = 135
            if jogador.status.sangramento > 0:
                txt_bleed = self.font_big.render("SANGRANDO!", True, (255, 0, 0))
                surface.blit(txt_bleed, (20, bleed_y))
                bleed_y += 30

            # STATUS DE REFÚGIO DA FOGUEIRA
            if getattr(jogador, "near_campfire", False):
                badge_rect = pygame.Rect(20, bleed_y, 185, 22)
                pygame.draw.rect(surface, (45, 25, 12), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 140, 30), badge_rect, 1, border_radius=4)
                pygame.draw.polygon(
                    surface,
                    (255, 150, 40),
                    [(27, bleed_y + 16), (32, bleed_y + 6), (37, bleed_y + 16)],
                )
                txt_fire = self.font_small.render("REFUGIO DO FOGO (+REC)", True, (255, 215, 120))
                surface.blit(txt_fire, (42, bleed_y + 4))

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
