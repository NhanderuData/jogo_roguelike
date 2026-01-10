# src/graphics/renderer.py
import pygame
from core import config
from . import recursos
from . import shaders
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)
        
        # 1. Luz do Player (Fura a noite)
        self.luz_player = self.criar_luz_gradiente(raio=100) 

        # 2. Luz do Disparo (Fura a noite)
        self.luz_projetil = self.criar_luz_gradiente(raio=80)
        
        # 3. GLOW do Disparo (Adiciona Cor Laranja) - NOVO!
        self.glow_projetil = self.criar_glow_colorido(raio=80, cor=(50, 30, 0))

    def criar_luz_gradiente(self, raio):
        luz = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        passos = 30
        for i in range(passos):
            fracao = 1 - (i / passos)
            alpha = int(255 * (fracao ** 2))
            raio_atual = int(raio * (i / passos))
            if raio_atual > 0:
                # Desenha preto com alpha para usar no modo SUBTRACT
                pygame.draw.circle(luz, (0, 0, 0, alpha), (raio, raio), raio_atual)
        return luz

    def criar_glow_colorido(self, raio, cor):
        # Cria uma luz colorida para somar (BLEND_ADD)
        glow = pygame.Surface((raio * 2, raio * 2), pygame.SRCALPHA)
        passos = 20
        for i in range(passos):
            fracao = 1 - (i / passos)
            alpha = int(100 * (fracao ** 2)) # Mais suave
            raio_atual = int(raio * (i / passos))
            if raio_atual > 0:
                # Cor + Alpha
                r, g, b = cor
                pygame.draw.circle(glow, (r, g, b, alpha), (raio, raio), raio_atual)
        return glow

    # ... (Manter métodos obter_rect_ancorado, ancorar_na_base, gerar_sombra_projetada IGUAIS) ...
    def obter_rect_ancorado(self, imagem, grid_x, grid_y, ajuste_x=0, ajuste_y=0):
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        rect = imagem.get_rect()
        rect.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect.bottom = screen_y + config.TAMANHO_TILE + ajuste_y
        return rect

    def ancorar_na_base(self, imagem, grid_x, grid_y, ajuste_x=0):
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        rect_img = imagem.get_rect()
        rect_img.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect_img.bottom = screen_y + config.TAMANHO_TILE
        return rect_img

    def gerar_sombra_projetada(self, sprite, inclinacao=-1.2):
        if not sprite: return None
        try:
            mask = pygame.mask.from_surface(sprite)
            sombra = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
            largura, altura = sombra.get_size()
            sombra = pygame.transform.scale(sombra, (largura, int(altura * 0.4)))
            sombra = pygame.transform.rotozoom(sombra, 20 * inclinacao, 1.0)
            return sombra
        except: return None

    def draw(self, surface, mapa_obj, cor_noite=(0, 0, 0, 0)):
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y
        
        # 1. CHÃO (Manter código igual, resumido aqui)
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

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
                if img: surface.blit(img, (screen_x, screen_y))
                
                # Bordas
                if tile.tipo == "blue_ground":
                    viz_top = mapa_obj.obter_tile(x, y - 1)
                    if viz_top and viz_top.tipo not in ["blue_ground",'deep_water', "parede"]:
                        bord = recursos.SPRITES.get("border_top")
                        if bord: surface.blit(bord, (screen_x, screen_y))
                    viz_bot = mapa_obj.obter_tile(x, y + 1)
                    if viz_bot and viz_bot.tipo not in ["blue_ground",'deep_water', "parede"]:
                        bord = recursos.SPRITES.get("border_bottom")
                        if bord: surface.blit(bord, (screen_x, screen_y))
                    viz_left = mapa_obj.obter_tile(x - 1, y)
                    if viz_left and viz_left.tipo not in ["blue_ground",'deep_water', "parede"]:
                        bord = recursos.SPRITES.get("border_left")
                        if bord: surface.blit(bord, (screen_x, screen_y))
                    viz_right = mapa_obj.obter_tile(x + 1, y)
                    if viz_right and viz_right.tipo not in ["blue_ground",'deep_water', "parede"]:
                        bord = recursos.SPRITES.get("border_right")
                        if bord: surface.blit(bord, (screen_x, screen_y))

        # 2. ENTIDADES E PROJÉTEIS
        render_list = []
        for ent in mapa_obj.entidades:
            if not ent.image: continue
            if not hasattr(ent, 'sombra_cache') or ent.sombra_cache is None:
                 ent.sombra_cache = self.gerar_sombra_projetada(ent.image)
            if ent.sombra_cache:
                rect_sombra = self.ancorar_na_base(ent.sombra_cache, ent.x, ent.y, ajuste_x=8)
                render_list.append((rect_sombra.bottom - 5, ent.sombra_cache, rect_sombra.x, rect_sombra.y))
            
            img_final = ent.image
            if hasattr(ent, 'dano_timer') and ent.dano_timer > 0:
                img_hit = shaders.aplicar_flash_branco(ent.image)
                if img_hit: img_final = img_hit
                ent.dano_timer -= 1
            rect_ent = self.obter_rect_ancorado(img_final, ent.x, ent.y, ajuste_x=ent.offset_x, ajuste_y=ent.offset_y)
            render_list.append((rect_ent.bottom, img_final, rect_ent.x, rect_ent.y))

        for p in mapa_obj.projeteis:
            if p.image and p.active:
                px = p.x * config.TAMANHO_TILE - cam_x
                py = p.y * config.TAMANHO_TILE - cam_y
                rect = p.image.get_rect(center=(px, py))
                render_list.append((rect.bottom, p.image, rect.x, rect.y))

        render_list.sort(key=lambda item: item[0])
        for _, img, x, y in render_list:
            surface.blit(img, (x, y))

        # --- 3. ILUMINAÇÃO (AQUI ESTÁ A CORREÇÃO VISUAL) ---
        if cor_noite[3] > 0:
            overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
            overlay.fill(cor_noite)

            # A. FURA A NOITE (Deixa transparente onde tem luz)
            if mapa_obj.jogador:
                px = mapa_obj.jogador.x * config.TAMANHO_TILE - cam_x + 16
                py = mapa_obj.jogador.y * config.TAMANHO_TILE - cam_y + 16
                overlay.blit(self.luz_player, (px - 100, py - 100), special_flags=pygame.BLEND_RGBA_SUB)

            for p in mapa_obj.projeteis:
                if not p.active: continue
                px = p.x * config.TAMANHO_TILE - cam_x + 16
                py = p.y * config.TAMANHO_TILE - cam_y + 16
                overlay.blit(self.luz_projetil, (px - 80, py - 80), special_flags=pygame.BLEND_RGBA_SUB)

            surface.blit(overlay, (0, 0))

            # B. ADICIONA GLOW (Desenha cor laranja por cima pra brilhar)
            # Isso garante que a luz apareça mesmo se o chão for escuro
            for p in mapa_obj.projeteis:
                if not p.active: continue
                px = p.x * config.TAMANHO_TILE - cam_x + 16
                py = p.y * config.TAMANHO_TILE - cam_y + 16
                # Desenha o brilho laranja com modo SOMA (ADD)
                surface.blit(self.glow_projetil, (px - 80, py - 80), special_flags=pygame.BLEND_RGBA_ADD)

        # 4. Pós-Processamento
        surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # UI e Debug
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi": self.desenhar_barra_flutuante(surface, ent)
        
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)
    
    def desenhar_barra_flutuante(self, surface, ent):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        screen_x = ent.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.y * config.TAMANHO_TILE - self.camera.camera_y
        largura, altura = 32, 4
        x, y = screen_x, screen_y - 12
        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, largura, altura), 1)