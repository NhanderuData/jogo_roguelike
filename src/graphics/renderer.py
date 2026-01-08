import pygame
from . import config
from . import recursos
from . import shaders
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera
        # Pré-carrega o shader de vinheta para não pesar o loop
        self.vignette_surf = shaders.gerar_vignette(config.LARGURA_TELA, config.ALTURA_TELA)

    def obter_rect_ancorado(self, imagem, grid_x, grid_y, ajuste_x=0, ajuste_y=0, off_z=0):
        """ Alinha a base da imagem com o chão do tile, respeitando o Eixo Z """
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        rect = imagem.get_rect()
        
        # Centraliza no X e ancora no fundo (bottom) no Y
        rect.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect.bottom = screen_y + config.TAMANHO_TILE - off_z + ajuste_y
        return rect
    def ancorar_na_base(self, imagem, grid_x, grid_y, ajuste_y=0, ajuste_x=0):
        """ Posiciona a sombra no chão real (Z=0) """
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
        
        # --- CULLING ---
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

        render_list = []

        # --- FASE 1 & 2: TERRENO ---
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile = mapa_obj.obter_tile(x, y)
                if not tile: continue

                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                off_z = tile.get_offset_y()

                # Borda do Degrau
                if tile.z_level > 0:
                    pygame.draw.rect(surface, (70, 40, 20), 
                                   (screen_x, screen_y - off_z + 16, config.TAMANHO_TILE, off_z + 16))

                img_key = "grass"
                if tile.tipo == "rocha": img_key = "rock"
                elif tile.tipo == "parede": img_key = "wall"

                img_chao = recursos.SPRITES.get(img_key)
                if img_chao:
                    surface.blit(img_chao, (screen_x, screen_y - off_z))

        # --- FASE 3: ENTIDADES ---
        for ent in mapa_obj.entidades:
            if not ent.image: continue # PROTEÇÃO: Pula se não tiver imagem
            
            tile_atual = mapa_obj.obter_tile(ent.x, ent.y)
            z_ent = tile_atual.get_offset_y() if tile_atual else 0

            # Sombra
            if not hasattr(ent, 'sombra_cache') or ent.sombra_cache is None:
                ent.sombra_cache = self.gerar_sombra_projetada(ent.image)
            
            rect_sombra = self.ancorar_na_base(ent.sombra_cache, ent.x, ent.y, ajuste_x=8)
            render_list.append((ent.y - 0.1, ent.sombra_cache, rect_sombra.x, rect_sombra.y))

            # Corpo com Shader de Dano
            img_final = ent.image
            if hasattr(ent, 'dano_timer') and ent.dano_timer > 0:
                # O shader agora se chama aplicar_flash_branco corretamente
                img_hit = shaders.aplicar_flash_branco(ent.image)
                if img_hit: img_final = img_hit
                ent.dano_timer -= 1

            rect_ent = self.obter_rect_ancorado(img_final, ent.x, ent.y, 
                                             ajuste_x=ent.offset_x, ajuste_y=ent.offset_y, off_z=z_ent)
            render_list.append((ent.y, img_final, rect_ent.x, rect_ent.y))

        # --- FASE 4: DESENHO E ORDENAÇÃO ---
        render_list.sort(key=lambda item: item[0])
        for _, img, x, y in render_list:
            surface.blit(img, (x, y))

        # --- FASE 5: SHADERS TELA CHEIA (Vinheta) ---
        # Aplica a vinheta por cima do cenário para foco visual
        surface.blit(self.vignette_surf, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

        # 2. Agora o Shader de Ambientação
        # Descobrimos o bioma atual baseado na posição do jogador
        tile_jogador = mapa_obj.obter_tile(int(mapa_obj.jogador.x), int(mapa_obj.jogador.y))

        if tile_jogador:
            # Decidimos a cor baseada no tipo de terreno ou uma variável de bioma
            # Se você tiver tile.bioma, use ele. Se não, vamos simular pelo tipo:
            tipo_provisorio = "ruinas" if tile_jogador.tipo in ["parede", "terra"] else "floresta"
            
            cor_clima = shaders.shader_ambientacao(tipo_provisorio)
            
            if cor_clima:
                # Criamos uma superfície temporária do tamanho da tela
                overlay = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA), pygame.SRCALPHA)
                overlay.fill(cor_clima)
                # Desenha por cima de tudo com modo de mistura suave
                surface.blit(overlay, (0, 0))

        # --- FASE 6: UI E DEBUG ---
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi":
                t_hp = mapa_obj.obter_tile(ent.x, ent.y)
                off_hp = t_hp.get_offset_y() if t_hp else 0
                self.desenhar_barra_flutuante(surface, ent, off_hp)
        
        for p in mapa_obj.projeteis: p.draw(surface, cam_x, cam_y)
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)

    def desenhar_barra_flutuante(self, surface, ent, off_z):
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        screen_x = ent.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.y * config.TAMANHO_TILE - self.camera.camera_y - off_z
        
        largura, altura = 32, 4
        x, y = screen_x, screen_y - 12
        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0, 0, 0), (x, y, largura, altura), 1)