# src/renderer.py
import pygame
from . import config
from . import recursos
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera

    def centralizar(self, imagem, grid_x, grid_y, ajuste_y=0, ajuste_x=0):
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        rect_img = imagem.get_rect()
        rect_img.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect_img.centery = screen_y + (config.TAMANHO_TILE // 2) + ajuste_y
        return rect_img

    def ancorar_na_base(self, imagem, grid_x, grid_y, ajuste_y=0, ajuste_x=0):
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        rect_img = imagem.get_rect()
        rect_img.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect_img.bottom = screen_y + config.TAMANHO_TILE + ajuste_y
        return rect_img

    def gerar_sombra_projetada(self, sprite, inclinacao=-1.2):
        mask = pygame.mask.from_surface(sprite)
        sombra = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        largura, altura = sombra.get_size()
        sombra = pygame.transform.scale(sombra, (largura, int(altura * 0.4)))
        sombra = pygame.transform.rotozoom(sombra, 20 * inclinacao, 1.0)
        return sombra

    def draw(self, surface, mapa_obj):
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y
        
        # Culling
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

        render_list = []

        # --- FASE 1 & 2: CHÃO, BORDAS E ROCHAS ---
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = mapa_obj.obter_tile(x, y)
                if not tile: continue

                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                off_z = tile.get_offset_y()

                # 1. Desenha Borda de elevação (Degrau)
                if tile.z_level > 0:
                    pygame.draw.rect(surface, (70, 40, 20), 
                                   (screen_x, screen_y - off_z + 16, config.TAMANHO_TILE, off_z + 16))

                # 2. Identifica o Sprite pelo TIPO do tile (Biomas)
                img_key = "grass" # Padrão
                if tile.tipo == "rocha": img_key = "rock"
                elif tile.tipo == "terra": img_key = "grass" # Ou um sprite de terra se tiver
                elif tile.tipo == "parede": img_key = "wall"

                img_chao = recursos.SPRITES.get(img_key)
                if img_chao:
                    # Desenha o tile respeitando o Z
                    surface.blit(img_chao, (screen_x, screen_y - off_z))

        # --- FASE 3: ENTIDADES (Lhama e Mobs) ---
        for ent in mapa_obj.entidades:
            tile_atual = mapa_obj.obter_tile(ent.x, ent.y)
            z_ent = tile_atual.get_offset_y() if tile_atual else 0

            # Sombra no chão real (Z=0)
            if not hasattr(ent, 'sombra_cache') or ent.sombra_cache is None:
                ent.sombra_cache = self.gerar_sombra_projetada(ent.image)
            
            rect_sombra = self.ancorar_na_base(ent.sombra_cache, ent.x, ent.y, ajuste_x=8)
            render_list.append((ent.y - 0.1, ent.sombra_cache, rect_sombra.x, rect_sombra.y))

            # Corpo com compensação de altura
            rect_ent = self.centralizar(ent.image, ent.x, ent.y, ajuste_y=ent.offset_y - z_ent)
            render_list.append((ent.y, ent.image, rect_ent.x, rect_ent.y))

        # --- FASE 4: ORDENAÇÃO (Z-Sort) ---
        render_list.sort(key=lambda item: item[0])
        for _, img, x, y in render_list:
            surface.blit(img, (x, y))

        # --- FASE 5: UI, EFEITOS E DEBUG ---
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi":
                t_hp = mapa_obj.obter_tile(ent.x, ent.y)
                off_hp = t_hp.get_offset_y() if t_hp else 0
                # Passar o off_hp para a barra não ficar "dentro" do degrau
                self.desenhar_barra_flutuante(surface, ent, off_hp)
        
        for p in mapa_obj.projeteis: p.draw(surface, cam_x, cam_y)
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        # Chama o seu arquivo debug.py da raiz
        debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def desenhar_barra_flutuante(self, surface, ent, off_z):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        screen_x = ent.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.y * config.TAMANHO_TILE - self.camera.camera_y - off_z
        # ... (restante da lógica da barra igual)