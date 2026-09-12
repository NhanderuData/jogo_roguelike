import math
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

    def draw(self, surface, jogador, audio=None, mouse_pos=(0, 0), time_system=None, mapa=None):
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
                bleed_y += 26

            # BUFF: VISÃO NOTURNA (Cenoura)
            if getattr(jogador.status, "night_vision_timer", 0) > 0:
                t = int(jogador.status.night_vision_timer)
                badge_rect = pygame.Rect(20, bleed_y, 185, 22)
                pygame.draw.rect(surface, (18, 42, 28), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (80, 240, 140), badge_rect, 1, border_radius=4)
                txt_nv = self.font_small.render(f"VISAO NOTURNA ({t}s)", True, (160, 255, 190))
                surface.blit(txt_nv, (32, bleed_y + 4))
                bleed_y += 26

            # BUFF: REGENERAÇÃO (Beterraba, Repolho, etc.)
            if getattr(jogador.status, "regen_timer", 0) > 0:
                t = int(jogador.status.regen_timer)
                badge_rect = pygame.Rect(20, bleed_y, 185, 22)
                pygame.draw.rect(surface, (45, 18, 30), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (255, 80, 140), badge_rect, 1, border_radius=4)
                txt_reg = self.font_small.render(f"REGENERACAO (+HP {t}s)", True, (255, 170, 200))
                surface.blit(txt_reg, (32, bleed_y + 4))
                bleed_y += 26

            # DEBUFF: TONTURA / ALUCINÓGENO (Cogumelo Estranho)
            if getattr(jogador.status, "dizziness_timer", 0) > 0:
                t = int(jogador.status.dizziness_timer)
                badge_rect = pygame.Rect(20, bleed_y, 185, 22)
                pygame.draw.rect(surface, (35, 15, 45), badge_rect, border_radius=4)
                pygame.draw.rect(surface, (200, 70, 255), badge_rect, 1, border_radius=4)
                txt_dizzy = self.font_small.render(f"TONTURA ({t}s)", True, (230, 160, 255))
                surface.blit(txt_dizzy, (32, bleed_y + 4))
                bleed_y += 26

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

        if mapa and hasattr(mapa, "obter_decoracao_colhivel_proxima") and jogador:
            proximo = mapa.obter_decoracao_colhivel_proxima(jogador.x, jogador.y, raio=1.6)
            if proximo:
                _, _, item_nome = proximo
                self._draw_interaction_prompt(surface, f"[E] Colher {item_nome}")
            else:
                npc_perto = self._obter_npc_proximo(mapa, jogador.x, jogador.y, raio=2.0)
                if npc_perto:
                    self._draw_interaction_prompt(surface, f"[E] Falar com {npc_perto.nome}")

        self._draw_npc_dialogs(surface, mapa, jogador)

    def _obter_npc_proximo(self, mapa, x, y, raio=2.0):
        if not mapa or not hasattr(mapa, "entidades"):
            return None
        closest = None
        min_d = raio
        for ent in mapa.entidades:
            if getattr(ent, "role", None) == "npc":
                d = math.hypot(ent.x - x, ent.y - y)
                if d < min_d:
                    min_d = d
                    closest = ent
        return closest

    def _draw_npc_dialogs(self, surface, mapa, jogador):
        if not mapa or not hasattr(mapa, "entidades") or not jogador:
            return
        for ent in mapa.entidades:
            ai = getattr(ent, "ai", None)
            if getattr(ent, "role", None) == "npc" and ai and getattr(ai, "current_dialog", None):
                dist = math.hypot(ent.x - jogador.x, ent.y - jogador.y)
                if dist <= 10.0:
                    self._draw_speech_bubble(surface, ent.nome, ai.current_dialog)
                    break

    def _draw_speech_bubble(self, surface, npc_nome, texto):
        w = min(720, surface.get_width() - 80)
        padding = 16
        words = texto.split()
        lines = []
        cur_line = []
        for word in words:
            test_line = " ".join(cur_line + [word])
            if self.font.size(test_line)[0] > w - padding * 2:
                lines.append(" ".join(cur_line))
                cur_line = [word]
            else:
                cur_line.append(word)
        if cur_line:
            lines.append(" ".join(cur_line))

        line_height = self.font.get_linesize()
        h = 44 + len(lines) * line_height + padding
        cx = surface.get_width() // 2
        y = surface.get_height() - h - 110

        bg_rect = pygame.Rect(cx - w // 2, y, w, h)
        bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (16, 20, 26, 240), (0, 0, w, h), border_radius=10)
        pygame.draw.rect(bg_surf, (240, 185, 70, 240), (0, 0, w, h), 2, border_radius=10)
        surface.blit(bg_surf, (bg_rect.x, bg_rect.y))

        # Diamond icon
        icon_cx = bg_rect.x + padding + 6
        icon_cy = bg_rect.y + 22
        pts = [(icon_cx, icon_cy - 6), (icon_cx + 6, icon_cy), (icon_cx, icon_cy + 6), (icon_cx - 6, icon_cy)]
        pygame.draw.polygon(surface, (255, 215, 90), pts)

        name_surf = self.font_big.render(npc_nome, True, (255, 215, 90))
        surface.blit(name_surf, (bg_rect.x + padding + 18, bg_rect.y + 10))

        for i, line in enumerate(lines):
            line_surf = self.font.render(line, True, (245, 245, 245))
            surface.blit(line_surf, (bg_rect.x + padding, bg_rect.y + 42 + i * line_height))


    def _draw_interaction_prompt(self, surface, text):
        txt_surf = self.font.render(text, True, (255, 240, 180))
        padding_x, padding_y = 14, 7
        w = txt_surf.get_width() + padding_x * 2
        h = txt_surf.get_height() + padding_y * 2
        cx = surface.get_width() // 2
        cy = surface.get_height() - 72

        bg_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
        bg_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (20, 25, 30, 210), (0, 0, w, h), border_radius=8)
        pygame.draw.rect(bg_surf, (255, 200, 60, 240), (0, 0, w, h), 2, border_radius=8)
        surface.blit(bg_surf, (bg_rect.x, bg_rect.y))
        surface.blit(txt_surf, (cx - txt_surf.get_width() // 2, cy - txt_surf.get_height() // 2))

    def _draw_weapons(self, surface, jogador):
        weapons = jogador.weapons
        if not weapons or not hasattr(weapons, "current"):
            return

        unlocked_list = getattr(weapons, "unlocked_weapons", None)
        if not unlocked_list:
            unlocked_list = [w for w in weapons.slot_order if w in weapons.unlocked]
        if not unlocked_list:
            unlocked_list = [weapons.current_id]

        curr_id = weapons.current_id
        curr_idx = unlocked_list.index(curr_id) if curr_id in unlocked_list else 0
        total_unlocked = len(unlocked_list)

        slot_size = 58
        gap = 8
        base_slots = list(weapons.slot_order)
        if curr_id not in base_slots:
            visible_slots = base_slots + [curr_id]
        else:
            visible_slots = base_slots

        total_width = len(visible_slots) * slot_size + (len(visible_slots) - 1) * gap
        scr_w = surface.get_width()
        scr_h = surface.get_height()
        start_x = scr_w - total_width - 20
        y = scr_h - slot_size - 18

        for slot_idx, weapon_id in enumerate(visible_slots):
            x = start_x + slot_idx * (slot_size + gap)
            is_unlocked = weapon_id in weapons.unlocked
            is_selected = (weapon_id == curr_id)
            definition = weapons.content.weapons.get(weapon_id)
            if not definition:
                continue

            bg_color = (32, 38, 46) if is_selected else ((18, 22, 26) if is_unlocked else (12, 13, 16))
            border_color = (255, 215, 65) if is_selected else ((80, 90, 100) if is_unlocked else (42, 46, 52))
            border_width = 3 if is_selected else 1

            pygame.draw.rect(surface, bg_color, (x, y, slot_size, slot_size), border_radius=6)
            pygame.draw.rect(surface, border_color, (x, y, slot_size, slot_size), border_width, border_radius=6)

            # Número do atalho (1 a 6) ou estrela para arma especial equipada
            num_color = (255, 215, 65) if is_selected else ((180, 185, 195) if is_unlocked else (75, 80, 88))
            label_text = str(slot_idx + 1) if slot_idx < len(base_slots) else "★"
            num_surf = self.font_small.render(label_text, True, num_color)
            surface.blit(num_surf, (x + 5, y + 3))

            if is_unlocked:
                icon = self._scaled_icon(definition.sprite, (slot_size - 8, slot_size - 8))
                if icon:
                    surface.blit(icon, (x + 4, y + 4))
            else:
                lock_txt = self.font_small.render("[LOCK]", True, (75, 80, 88))
                surface.blit(lock_txt, (x + (slot_size - lock_txt.get_width()) // 2, y + 22))

        weapon = weapons.current
        name = self.font.render(weapon.name, True, (255, 240, 200))
        surface.blit(name, (start_x, y - 24))

        if weapon.kind == "ranged":
            magazine = weapons.magazines.get(weapons.current_id, 0)
            reserve = jogador.inventory.ammo_count(weapon.ammo_type) if hasattr(jogador, "inventory") else 0
            color = (240, 75, 65) if magazine == 0 else config.BRANCO
            ammo_str = f"{magazine} / {reserve}"
            if weapon.ammo_type:
                ammo_str += f" ({weapon.ammo_type.upper()})"
            ammo = self.font.render(ammo_str, True, color)
            ammo_rect = ammo.get_rect(topright=(scr_w - 20, y - 24))
            surface.blit(ammo, ammo_rect)
        elif weapon.kind == "melee":
            melee_tag = self.font_small.render("CORPO A CORPO", True, (180, 220, 255))
            ammo_rect = melee_tag.get_rect(topright=(scr_w - 20, y - 20))
            surface.blit(melee_tag, ammo_rect)

        # Barra separadora sutil
        pygame.draw.line(surface, (45, 52, 60), (start_x, y - 8), (start_x + total_width, y - 8), 1)

        if weapons.is_reloading:
            width = total_width
            pygame.draw.rect(surface, (30, 30, 35), (start_x, y - 6, width, 4), border_radius=2)
            pygame.draw.rect(
                surface,
                (245, 195, 60),
                (start_x, y - 6, int(width * weapons.reload_progress), 4),
                border_radius=2,
            )
