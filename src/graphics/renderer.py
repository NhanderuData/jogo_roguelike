import pygame
from core import config
from graphics import recursos
from graphics import shaders
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)
        
        # Luz do Player (Fura a escuridão - Branca/Amarelada)
        self.luz_player = self.criar_luz_gradiente(raio=100, cor=(255, 255, 220)) 
        
        # Luz do Projétil (Glow Aditivo - Laranja/Avermelhada para destacar)
        self.luz_projetil = self.criar_luz_gradiente(raio=50, cor=(255, 100, 50))

    def criar_luz_gradiente(self, raio, cor=(255, 255, 255)):
        # Cria uma superfície que suporta transparência
        luz = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        passos = 20
        r, g, b = cor
        for i in range(passos):
            fracao = 1 - (i / passos)
            # Alpha diminui conforme afasta do centro
            alpha = int(100 * (fracao ** 2)) 
            raio_atual = int(raio * (i / passos))
            if raio_atual > 0:
                pygame.draw.circle(luz, (r, g, b, alpha), (raio, raio), raio_atual)
        return luz

    def gerar_sombra_projetada(self, sprite, escala=1.0, inclinacao=-1.2):
        if not sprite: return None
        try:
            mask = pygame.mask.from_surface(sprite)
            sombra = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
            largura, altura = sombra.get_size()
            sombra = pygame.transform.scale(sombra, (int(largura * escala), int(altura * 0.4 * escala)))
            sombra = pygame.transform.rotozoom(sombra, 20 * inclinacao, 1.0)
            return sombra
        except Exception:
            return None

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
                
                img_key = "grass"
                if tile.tipo == "rocha": img_key = "rock"
                elif tile.tipo == "parede": img_key = "wall"
                elif tile.tipo == "blue_ground": img_key = "blue_ground"
                elif tile.tipo == "estrada": img_key = "estrada"
                elif tile.tipo == "deep_water": img_key = "deep_water"
                elif tile.tipo == "sand": img_key = "sand"
                
                img = recursos.SPRITES.get(img_key)
                if img: 
                    render_queue.append((config.LAYER_CHAO, screen_y, img, screen_x, screen_y))
                
                if tile.tipo == "blue_ground":
                    self.adicionar_bordas(mapa_obj, x, y, screen_x, screen_y, render_queue)

        # Entidades
        for ent in mapa_obj.entidades:
            if not hasattr(ent, 'sprite') or not ent.sprite.image: continue
            
            physics = ent.physics
            sprite = ent.sprite
            screen_x = physics.x * config.TAMANHO_TILE - cam_x
            screen_y = physics.y * config.TAMANHO_TILE - cam_y
            
            img_w = sprite.image.get_width()
            img_h = sprite.image.get_height()
            draw_x = screen_x + (config.TAMANHO_TILE // 2) - (img_w // 2) + sprite.offset_x
            draw_y = screen_y + config.TAMANHO_TILE - img_h + sprite.offset_y

            # Sombra
            if not sprite.sombra_cache:
                sprite.sombra_cache = self.gerar_sombra_projetada(sprite.image, sprite.scale_sombra)
            
            if sprite.sombra_cache:
                s_w = sprite.sombra_cache.get_width()
                s_h = sprite.sombra_cache.get_height()
                
                sombra_x = draw_x + (img_w // 2) - (s_w // 2)
                pixel_base_y = (physics.y * config.TAMANHO_TILE) + config.TAMANHO_TILE - cam_y
                sombra_y = pixel_base_y - (s_h // 2) - 2 
                render_queue.append((config.LAYER_SOMBRA, screen_y, sprite.sombra_cache, sombra_x, sombra_y))

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

        # --- 2. ESCURIDÃO AMBIENTAL (Subtractive) ---
        if cor_noite[3] > 0:
            self.aplicar_escuridao(surface, mapa_obj, cam_x, cam_y, cor_noite)

        # --- 3. LUZES ADITIVAS / GLOW (Additive) ---
        # Essas luzes brilham mesmo de dia!
        self.aplicar_glows(surface, mapa_obj, cam_x, cam_y)

        # Pós-Processamento e UI
        surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi": self.desenhar_barra_flutuante(surface, ent)
        
        for txt in mapa_obj.textos:
            txt.draw(surface, cam_x, cam_y)
            
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        # --- 4. DEBUG CONTROLADO PELO CONFIG ---
        if config.DEBUG_MODE:
             debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def adicionar_bordas(self, mapa_obj, x, y, sx, sy, queue):
        vizinhos = [
            (0, -1, "border_top"), (0, 1, "border_bottom"), 
            (-1, 0, "border_left"), (1, 0, "border_right")
        ]
        for dx, dy, img_key in vizinhos:
            viz = mapa_obj.obter_tile(x + dx, y + dy)
            if viz and viz.tipo not in ["blue_ground", 'deep_water', "parede"]:
                bord = recursos.SPRITES.get(img_key)
                if bord: queue.append((config.LAYER_CHAO, sy, bord, sx, sy))

    def aplicar_escuridao(self, surface, mapa_obj, cam_x, cam_y, cor_noite):
        """Aplica a camada de noite e recorta a visão do jogador (Luz que 'fura' o escuro)"""
        overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill(cor_noite)

        # Luz Player (Recorta a escuridão)
        if mapa_obj.jogador:
            px = mapa_obj.jogador.physics.x * config.TAMANHO_TILE - cam_x + (config.TAMANHO_TILE // 2)
            py = mapa_obj.jogador.physics.y * config.TAMANHO_TILE - cam_y + (config.TAMANHO_TILE // 2)
            # BLEND_RGBA_SUB remove a cor preta do overlay (criando transparência)
            overlay.blit(self.luz_player, 
                            (px - self.luz_player.get_width()//2, py - self.luz_player.get_height()//2), 
                            special_flags=pygame.BLEND_RGBA_SUB)
        
        surface.blit(overlay, (0, 0))

    def aplicar_glows(self, surface, mapa_obj, cam_x, cam_y):
        """Aplica luzes coloridas que brilham por cima de tudo (Neon/Magia)"""
        # Projéteis
        for p in mapa_obj.projeteis:
            if not p.active: continue
            px = p.x * config.TAMANHO_TILE - cam_x
            py = p.y * config.TAMANHO_TILE - cam_y
            
            lx = px - self.luz_projetil.get_width() // 2
            ly = py - self.luz_projetil.get_height() // 2
            
            # BLEND_ADD soma a cor da luz com a tela (brilha no escuro e no claro)
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