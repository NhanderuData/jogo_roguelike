# src/renderer.py
import pygame
from . import config
from . import recursos
import debug

class Renderer:
    def __init__(self, camera):
        self.camera = camera

    def centralizar(self, imagem, grid_x, grid_y, ajuste_y=0, ajuste_x=0):
        """ Posiciona o sprite pelo CENTRO do tile (Para o corpo do personagem/objeto) """
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        
        rect_img = imagem.get_rect()
        # Pivô Central: Meio do tile exato
        rect_img.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect_img.centery = screen_y + (config.TAMANHO_TILE // 2) + ajuste_y
        
        return rect_img

    def ancorar_na_base(self, imagem, grid_x, grid_y, ajuste_y=0, ajuste_x=0):
        """ Posiciona o sprite pela BASE do tile (Para sombras nascerem no chão) """
        screen_x = grid_x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = grid_y * config.TAMANHO_TILE - self.camera.camera_y
        
        rect_img = imagem.get_rect()
        # Pivô na Base: Centralizado em X, mas encostado no fundo do tile em Y
        rect_img.centerx = screen_x + (config.TAMANHO_TILE // 2) + ajuste_x
        rect_img.bottom = screen_y + config.TAMANHO_TILE + ajuste_y
        
        return rect_img

    def gerar_sombra_projetada(self, sprite, inclinação=-1.2):
        """ Cria a silhueta preta e distorcida """
        mask = pygame.mask.from_surface(sprite)
        sombra = mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))
        largura, altura = sombra.get_size()
        # Achata a sombra verticalmente para dar perspectiva
        sombra = pygame.transform.scale(sombra, (largura, int(altura * 0.4)))
        # Inclina a sombra usando rotozoom
        sombra = pygame.transform.rotozoom(sombra, 20 * inclinação, 1.0)
        return sombra

    def desenhar_barra_flutuante(self, surface, ent):
        """ Desenha o HP acima da cabeça dos inimigos """
        if ent.hp <= 0 or ent.hp >= ent.hp_max: return 
        
        # Posição na tela baseada no grid
        screen_x = ent.x * config.TAMANHO_TILE - self.camera.camera_x
        screen_y = ent.y * config.TAMANHO_TILE - self.camera.camera_y
        
        largura, altura = 32, 4
        x = screen_x 
        y = screen_y - 12 # 12 pixels acima do centro

        pct = max(0, ent.hp / ent.hp_max)
        pygame.draw.rect(surface, (50, 0, 0), (x, y, largura, altura))
        pygame.draw.rect(surface, (255, 50, 50), (x, y, int(largura * pct), altura))
        pygame.draw.rect(surface, (0,0,0), (x, y, largura, altura), 1)

    def draw(self, surface, mapa_obj):
        tempo_agora = pygame.time.get_ticks()
        img_grass = recursos.SPRITES.get("grass")
        cam_x, cam_y = self.camera.camera_x, self.camera.camera_y

        # Culling: Renderiza apenas o que está na tela
        start_col = max(0, int(cam_x // config.TAMANHO_TILE))
        end_col = min(config.LARGURA_MAPA, start_col + (config.LARGURA_TELA // config.TAMANHO_TILE) + 2)
        start_row = max(0, int(cam_y // config.TAMANHO_TILE))
        end_row = min(config.ALTURA_MAPA, start_row + (config.ALTURA_TELA // config.TAMANHO_TILE) + 2)

        render_list = []

        # FASE 1: CHÃO
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                screen_x = x * config.TAMANHO_TILE - cam_x
                screen_y = y * config.TAMANHO_TILE - cam_y
                if img_grass: surface.blit(img_grass, (screen_x, screen_y))

        # FASE 2: OBJETOS (Cenário estático)
        for y in range(start_row, end_row):
            for x in range(start_col, end_col):
                tile_id = mapa_obj.grid[y][x]
                dado_bruto = None
                if tile_id == config.PAREDE: dado_bruto = recursos.SPRITES.get("wall")
                elif tile_id == config.ARVORE: dado_bruto = recursos.SPRITES.get("tree")

                if dado_bruto:
                    img_final = dado_bruto[0] if isinstance(dado_bruto, list) else dado_bruto
                    
                    # Sombra na BASE do tile
                    sombra_obj = self.gerar_sombra_projetada(img_final)
                    rect_sombra = self.ancorar_na_base(sombra_obj, x, y, ajuste_x=10)
                    render_list.append((y - 0.1, sombra_obj, rect_sombra.x, rect_sombra.y))
                    
                    # Objeto real no CENTRO do tile
                    rect_obj = self.centralizar(img_final, x, y)
                    render_list.append((y, img_final, rect_obj.x, rect_obj.y))

        # FASE 3: ENTIDADES (Lhama e Inimigos)
        for ent in mapa_obj.entidades:
            if ent.image:
                # 1. PEGA OU GERA A SOMBRA (Garante que nenhuma fique sem)
                if not hasattr(ent, 'sombra_cache') or ent.sombra_cache is None:
                    ent.sombra_cache = self.gerar_sombra_projetada(ent.image)
                
                img_sombra = ent.sombra_cache
                
                # 2. POSICIONA A SOMBaRA NA BASE (Pivô Y no fundo do tile)
                rect_sombra = self.ancorar_na_base(img_sombra, ent.x, ent.y, ajuste_x=8)
                render_list.append((ent.y - 0.1, img_sombra, rect_sombra.x, rect_sombra.y))
                
                # 3. POSICIONA O CORPO NO CENTRO (Pivô Central)
                rect_ent = self.centralizar(ent.image, ent.x, ent.y, ajuste_x=ent.offset_x, ajuste_y=ent.offset_y)
                render_list.append((ent.y, ent.image, rect_ent.x, rect_ent.y))

        # FASE 4: RENDER FINAL (Z-Sort)
        render_list.sort(key=lambda item: item[0])
        for _, img, x, y in render_list:
            surface.blit(img, (x, y))
            
        # FASE 5: UI e Efeitos
        for ent in mapa_obj.entidades:
            if ent.nome != "Heroi":
                self.desenhar_barra_flutuante(surface, ent)
        
        for p in mapa_obj.projeteis: p.draw(surface, cam_x, cam_y)
        for e in mapa_obj.efeitos: e.draw(surface, cam_x, cam_y)
        
        debug.desenhar_hitboxes(surface, self.camera, mapa_obj, config)