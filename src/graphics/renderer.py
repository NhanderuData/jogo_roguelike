# src/graphics/renderer.py
import pygame
from core import config
from graphics import recursos
from graphics import shaders
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)
        
        # Luzes (Mantém a lógica antiga de iluminação)
        self.luz_player = self.criar_luz_gradiente(raio=100) 
        self.luz_projetil = self.criar_luz_gradiente(raio=60)

    def criar_luz_gradiente(self, raio):
        luz = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        passos = 30
        for i in range(passos):
            fracao = 1 - (i / passos)
            alpha = int(255 * (fracao ** 2))
            raio_atual = int(raio * (i / passos))
            if raio_atual > 0:
                pygame.draw.circle(luz, (0, 0, 0, alpha), (raio, raio), raio_atual)
        return luz

    def gerar_sombra_projetada(self, sprite, escala=1.0, inclinacao=-1.2):
        if not sprite: return None
        try:
            mask = pygame.mask.from_surface(sprite)
            sombra = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
            largura, altura = sombra.get_size()
            # Achata a sombra
            sombra = pygame.transform.scale(sombra, (int(largura * escala), int(altura * 0.4 * escala)))
            # Inclina
            sombra = pygame.transform.rotozoom(sombra, 20 * inclinacao, 1.0)
            return sombra
        except Exception:
            return None

    def draw(self, surface, mapa_obj, cor_noite=(0, 0, 0, 0)):
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y
        
        # --- 1. PREPARAÇÃO DA FILA DE RENDERIZAÇÃO ---
        # Cada item é uma tupla: (LAYER, Y_SORT, IMAGEM, X, Y)
        render_queue = []

        # Limites da Câmera (Culling)
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

        # --- 2. DESENHO DO CHÃO (TILES) ---
        # Tiles de fundo desenhamos direto para performance, ou adicionamos na Layer 0
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = mapa_obj.obter_tile(x, y)
                if not tile: continue
                
                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                
                # Seleção de Sprite do Tile
                img_key = "grass"
                if tile.tipo == "rocha": img_key = "rock" # Chão rochoso
                elif tile.tipo == "parede": img_key = "wall"
                elif tile.tipo == "blue_ground": img_key = "blue_ground"
                elif tile.tipo == "estrada": img_key = "estrada"
                elif tile.tipo == "deep_water": img_key = "deep_water"
                elif tile.tipo == "sand": img_key = "sand"
                
                img = recursos.SPRITES.get(img_key)
                if img: 
                    # Adiciona na fila na camada mais baixa (CHAO)
                    # Usamos y * 32 como critério de ordenação secundária
                    render_queue.append((config.LAYER_CHAO, screen_y, img, screen_x, screen_y))
                
                # Bordas da Água (Decoração)
                if tile.tipo == "blue_ground":
                    self.adicionar_bordas(mapa_obj, x, y, screen_x, screen_y, render_queue)

        # --- 3. ENTIDADES (PLAYER, INIMIGOS, ÁRVORES) ---
        for ent in mapa_obj.entidades:
            # Pega dados via Componente Sprite e Física
            # Se a entidade não tiver sprite (bug), ignora
            if not hasattr(ent, 'sprite') or not ent.sprite.image: continue
            
            # Atalhos
            physics = ent.physics
            sprite = ent.sprite
            
            # Posição na tela
            screen_x = physics.x * config.TAMANHO_TILE - cam_x
            screen_y = physics.y * config.TAMANHO_TILE - cam_y
            
            # Centralização da imagem (usando offsets do componente visual)
            # A imagem é desenhada centrada no tile
            img_w = sprite.image.get_width()
            img_h = sprite.image.get_height()
            
            draw_x = screen_x + (config.TAMANHO_TILE // 2) - (img_w // 2) + sprite.offset_x
            draw_y = screen_y + config.TAMANHO_TILE - img_h + sprite.offset_y

            # A. Sombra (Sempre na Layer SOMBRA)
            # Verifica cache
            if not sprite.sombra_cache:
                sprite.sombra_cache = self.gerar_sombra_projetada(sprite.image, sprite.scale_sombra)
            
            if sprite.sombra_cache:
                s_w = sprite.sombra_cache.get_width()
                s_h = sprite.sombra_cache.get_height()
                # A sombra fica no pé da entidade
                sombra_x = screen_x + (config.TAMANHO_TILE // 2) - (s_w // 2) + 8 # +8 deslocamento estético
                sombra_y = screen_y + config.TAMANHO_TILE - (s_h // 2) - 2
                
                render_queue.append((config.LAYER_SOMBRA, screen_y, sprite.sombra_cache, sombra_x, sombra_y))

            # B. Corpo (Na Layer definida pelo componente, geralmente CORPO)
            img_final = sprite.image
            
            # Efeito de Dano (Flash Branco)
            if hasattr(sprite, 'dano_timer') and sprite.dano_timer > 0:
                img_hit = shaders.aplicar_flash_branco(sprite.image)
                if img_hit: img_final = img_hit
                sprite.dano_timer -= 1
            
            # Adiciona corpo na fila
            render_queue.append((sprite.layer, screen_y, img_final, draw_x, draw_y))

        # --- 4. PROJÉTEIS ---
        for p in mapa_obj.projeteis:
            if p.image and p.active:
                px = p.x * config.TAMANHO_TILE - cam_x
                py = p.y * config.TAMANHO_TILE - cam_y
                rect = p.image.get_rect(center=(px, py))
                # Projéteis geralmente voam, Layer AÉREO
                render_queue.append((config.LAYER_AEREO, py, p.image, rect.x, rect.y))

        # --- 5. ORDENAÇÃO MÁGICA ---
        # Ordena por: 1º Camada (0 a 7), 2º Posição Y (Profundidade)
        render_queue.sort(key=lambda item: (item[0], item[1]))

        # --- 6. DESENHA TUDO ---
        for _, _, img, x, y in render_queue:
            surface.blit(img, (x, y))

        # --- 7. ILUMINAÇÃO (Igual ao anterior) ---
        if cor_noite[3] > 0:
            self.aplicar_iluminacao(surface, mapa_obj, cam_x, cam_y, cor_noite)

        # 8. Pós-Processamento e UI
        surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        
        # Barras de vida (UI do mundo)
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi": self.desenhar_barra_flutuante(surface, ent)
        
        # Textos flutuantes
        for txt in mapa_obj.textos:
            txt.draw(surface, cam_x, cam_y)
            
        # Efeitos (risco da espada)
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        # Debug
        # debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def adicionar_bordas(self, mapa_obj, x, y, sx, sy, queue):
        """Helper para adicionar bordas de água na layer correta"""
        # Checa vizinhos e adiciona bordas na Layer CHAO
        vizinhos = [
            (0, -1, "border_top"), (0, 1, "border_bottom"), 
            (-1, 0, "border_left"), (1, 0, "border_right")
        ]
        for dx, dy, img_key in vizinhos:
            viz = mapa_obj.obter_tile(x + dx, y + dy)
            if viz and viz.tipo not in ["blue_ground", 'deep_water', "parede"]:
                bord = recursos.SPRITES.get(img_key)
                if bord: queue.append((config.LAYER_CHAO, sy, bord, sx, sy))

    def aplicar_iluminacao(self, surface, mapa_obj, cam_x, cam_y, cor_noite):
        overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
        overlay.fill(cor_noite)

        # Luz Player
        if mapa_obj.jogador:
            # Correção para usar a posição do componente physics
            px = mapa_obj.jogador.physics.x * config.TAMANHO_TILE - cam_x + (config.TAMANHO_TILE // 2)
            py = mapa_obj.jogador.physics.y * config.TAMANHO_TILE - cam_y + (config.TAMANHO_TILE // 2)
            overlay.blit(self.luz_player, 
                            (px - self.luz_player.get_width()//2, py - self.luz_player.get_height()//2), 
                            special_flags=pygame.BLEND_RGBA_SUB)

        # Luz Projéteis
        for p in mapa_obj.projeteis:
            if not p.active: continue
            px = p.x * config.TAMANHO_TILE - cam_x
            py = p.y * config.TAMANHO_TILE - cam_y
            lx = px - self.luz_projetil.get_width() // 2
            ly = py - self.luz_projetil.get_height() // 2
            overlay.blit(self.luz_projetil, (lx, ly), special_flags=pygame.BLEND_RGBA_SUB)

        surface.blit(overlay, (0, 0))

    def desenhar_barra_flutuante(self, surface, ent):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        # Usa physics para posição
        screen_x = ent.physics.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.physics.y * config.TAMANHO_TILE - self.camera.camera_y
        largura, altura = 32, 4
        x, y = screen_x, screen_y - 12
        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, largura, altura), 1)