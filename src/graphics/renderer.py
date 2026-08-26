# src/graphics/renderer.py
import pygame
from core import config
from graphics import recursos
from graphics import shaders
from graphics.ambience import AmbientRenderer
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)
        
        # Luz do Projétil (Glow Aditivo - Laranja/Avermelhada para destacar)
        self.luz_projetil = self.criar_luz_gradiente(raio=50, cor=(255, 100, 50))
        self.ambience = AmbientRenderer()

    def criar_luz_gradiente(self, raio, cor=(255, 255, 255)):
        luz = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        passos = 20
        r, g, b = cor
        for i in range(passos):
            fracao = 1 - (i / passos)
            alpha = int(100 * (fracao ** 2)) 
            raio_atual = int(raio * (i / passos))
            if raio_atual > 0:
                pygame.draw.circle(luz, (r, g, b, alpha), (raio, raio), raio_atual)
        return luz

    # --- CORREÇÃO AQUI: Substituímos Rotação por SKEW (Cisalhamento) ---
    def gerar_sombra_realista(self, sprite_img, escala_tamanho=1.0):
        if not sprite_img: return None
        
        # 1. Cria a silhueta preta (Mask)
        try:
            mask = pygame.mask.from_surface(sprite_img)
            sombra_surf = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        except (pygame.error, ValueError, TypeError):
            return None

        # 2. Achata a sombra verticalmente (Escala Y)
        # 0.5 significa que a sombra terá metade da altura do objeto original
        w, h = sombra_surf.get_size()
        novo_h = int(h * 0.5 * escala_tamanho) 
        sombra_surf = pygame.transform.scale(sombra_surf, (w, novo_h))

        # 3. Aplica o Efeito SKEW (Inclina linha por linha)
        # Fator de inclinação (quanto maior, mais "deitada" a sombra para o lado)
        skew_factor = 0.6 
        offset_total = int(novo_h * skew_factor)
        largura_final = w + abs(offset_total)
        
        surface_final = pygame.Surface((largura_final, novo_h), pygame.SRCALPHA)
        
        # Loop "Pixel Perfect": Desloca cada linha de pixels para a direita
        # A linha de baixo (base) desloca 0. A linha de cima desloca o máximo.
        # Isso garante que a BASE continue no mesmo lugar!
        for i in range(novo_h):
            # Invertemos o i para que a base (y alto) tenha shift 0
            shift = int((novo_h - i) * skew_factor)
            
            # Pega uma linha da imagem achatada
            linha = sombra_surf.subsurface((0, i, w, 1))
            
            # Cola na nova superfície com o deslocamento
            surface_final.blit(linha, (shift, i))
            
        return surface_final

    def draw(self, surface, mapa_obj, cor_noite=(0, 0, 0, 0)):
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y
        
        # --- 1. RENDER QUEUE (Camadas) ---
        render_queue = []
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

        # Tiles
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = mapa_obj.obter_tile(x, y)
                if not tile: continue
                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                
                img_key = "terrain_grass"
                if tile.tipo == "rocha": img_key = "terrain_rubble"
                elif tile.tipo == "parede": img_key = "wall"
                elif tile.tipo in ("terra", "terrain_dirt"): img_key = "terrain_dirt"
                elif tile.tipo == "grass": img_key = "terrain_grass"
                elif tile.tipo == "blue_ground": img_key = "terrain_moss"
                elif tile.tipo == "estrada": img_key = "terrain_road"
                elif tile.tipo == "deep_water": img_key = "terrain_water"
                elif tile.tipo == "sand": img_key = "terrain_sand"
                elif tile.tipo == "coast": img_key = "terrain_coast"
                elif tile.tipo == "rubble": img_key = "terrain_rubble"
                elif tile.tipo == "mud": img_key = "terrain_mud"

                variation = (x * 31 + y * 17) % 3
                if variation == 1 and f"{img_key}_flip_x" in recursos.SPRITES:
                    img_key = f"{img_key}_flip_x"
                elif variation == 2 and f"{img_key}_flip_y" in recursos.SPRITES:
                    img_key = f"{img_key}_flip_y"
                
                img = recursos.SPRITES.get(img_key)
                if img: 
                    render_queue.append((config.LAYER_CHAO, screen_y, img, screen_x, screen_y))
                
                self.adicionar_transicoes(
                    mapa_obj, tile.tipo, x, y, screen_x, screen_y, render_queue
                )

        # Entidades
        for ent in mapa_obj.entidades:
            if not hasattr(ent, 'sprite') or not ent.sprite.image: continue
            
            physics = ent.physics
            sprite = ent.sprite
            screen_x = physics.x * config.TAMANHO_TILE - cam_x
            screen_y = physics.y * config.TAMANHO_TILE - cam_y
            
            img_w = sprite.image.get_width()
            img_h = sprite.image.get_height()
            
            # Posição onde o SPRITE será desenhado
            draw_x = screen_x + (config.TAMANHO_TILE // 2) - (img_w // 2) + sprite.offset_x
            draw_y = screen_y + config.TAMANHO_TILE - img_h + sprite.offset_y

            # --- Sombra (CORRIGIDO) ---
            # Só desenha sombra se não for Layer de chão e tiver escala configurada
            if sprite.scale_sombra > 0:
                if not sprite.sombra_cache:
                    # Gera a sombra com Skew
                    sprite.sombra_cache = self.gerar_sombra_realista(sprite.image, sprite.scale_sombra)
                
                if sprite.sombra_cache:
                    sombra = sprite.sombra_cache
                    s_h = sombra.get_height()
                    
                    # ALINHAMENTO:
                    # Como usamos Skew na base (shift=0 na base), o X da sombra é igual ao X do sprite.
                    # O Y da sombra deve alinhar o "pé" da sombra com o "pé" do sprite.
                    
                    sombra_x = draw_x 
                    # "Pé" do sprite = draw_y + img_h
                    # Queremos que "Pé" da sombra (sombra_y + s_h) seja igual a pé do sprite
                    sombra_y = (draw_y + img_h) - s_h - 2 # -2 pixels para subir um pouquinho e não vazar
                    
                    render_queue.append((config.LAYER_SOMBRA, screen_y, sombra, sombra_x, sombra_y))

            # Corpo
            img_final = sprite.image
            if hasattr(sprite, 'dano_timer') and sprite.dano_timer > 0:
                img_hit = shaders.aplicar_flash_branco(sprite.image)
                if img_hit: img_final = img_hit
                sprite.dano_timer -= 1
            render_queue.append((sprite.layer, screen_y, img_final, draw_x, draw_y))

        # Projéteis
        for p in mapa_obj.projeteis:
            if p.image and p.active:
                px = p.x * config.TAMANHO_TILE - cam_x
                py = p.y * config.TAMANHO_TILE - cam_y
                rect = p.image.get_rect(center=(px, py))
                render_queue.append((config.LAYER_AEREO, py, p.image, rect.x, rect.y))

        # Desenhar Camadas
        render_queue.sort(key=lambda item: (item[0], item[1]))
        for _, _, img, x, y in render_queue:
            surface.blit(img, (x, y))

        mapa_obj.particulas.draw(surface, cam_x, cam_y)

        # --- 2. ESCURIDÃO AMBIENTAL (Subtractive) ---
        if cor_noite[3] > 0:
            self.aplicar_escuridao(surface, mapa_obj, cam_x, cam_y, cor_noite)

        # --- 3. LUZES ADITIVAS / GLOW (Additive) ---
        self.aplicar_glows(surface, mapa_obj, cam_x, cam_y)

        self.ambience.draw(surface, mapa_obj)

        # Pós-Processamento e UI
        surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi": self.desenhar_barra_flutuante(surface, ent)
        
        for loot in mapa_obj.items_no_chao:
            loot.draw(surface, cam_x, cam_y)

        for txt in mapa_obj.textos:
            txt.draw(surface, cam_x, cam_y)
            
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        if config.DEBUG_MODE:
             debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def adicionar_transicoes(self, mapa_obj, tile_type, x, y, sx, sy, queue):
        neighbors = (
            (0, -1, "top"),
            (0, 1, "bottom"),
            (-1, 0, "left"),
            (1, 0, "right"),
        )
        land_types = {"coast", "grass", "terra", "rubble", "mud", "parede"}
        for dx, dy, side in neighbors:
            neighbor = mapa_obj.obter_tile(x + dx, y + dy)
            if not neighbor:
                continue

            prefix = None
            if tile_type == "sand" and neighbor.tipo in land_types:
                prefix = "coast_edge"
            elif tile_type == "blue_ground" and neighbor.tipo in {"sand", "coast"}:
                prefix = "sand_edge"
            elif tile_type == "deep_water" and neighbor.tipo == "blue_ground":
                prefix = "moss_edge"
            elif tile_type == "deep_water" and neighbor.tipo in {"sand", "coast"}:
                prefix = "sand_edge"

            image = recursos.SPRITES.get(f"{prefix}_{side}") if prefix else None
            if image:
                queue.append((config.LAYER_CHAO + 0.5, sy, image, sx, sy))

    def aplicar_escuridao(self, surface, mapa_obj, cam_x, cam_y, cor_noite):
        overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill(cor_noite)

        surface.blit(overlay, (0, 0))

    def aplicar_glows(self, surface, mapa_obj, cam_x, cam_y):
        for p in mapa_obj.projeteis:
            if not p.active: continue
            px = p.x * config.TAMANHO_TILE - cam_x
            py = p.y * config.TAMANHO_TILE - cam_y
            
            lx = px - self.luz_projetil.get_width() // 2
            ly = py - self.luz_projetil.get_height() // 2
            
            surface.blit(self.luz_projetil, (lx, ly), special_flags=pygame.BLEND_ADD)

    def desenhar_barra_flutuante(self, surface, ent):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        screen_x = ent.physics.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.physics.y * config.TAMANHO_TILE - self.camera.camera_y
        largura, altura = 32, 4
        x, y = screen_x, screen_y - 12
        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, largura, altura), 1)
