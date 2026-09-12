# src/debug.py
import pygame

_BLOCKED_TILE_OVERLAYS = {}


def _blocked_tile_overlay(tile_size):
    overlay = _BLOCKED_TILE_OVERLAYS.get(tile_size)
    if overlay is None:
        overlay = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, 100))
        _BLOCKED_TILE_OVERLAYS[tile_size] = overlay
    return overlay


def desenhar_hitboxes(surface, camera, mapa_obj, config):
    cam_x, cam_y = camera.camera_x, camera.camera_y
    tile_size = config.TAMANHO_TILE
    blocked_overlay = _blocked_tile_overlay(tile_size)

    # 1. Desenha Tiles Bloqueados (Vermelho)
    start_x = max(0, int(cam_x // tile_size))
    start_y = max(0, int(cam_y // tile_size))
    end_x = min(
        mapa_obj.largura,
        start_x + config.LARGURA_TELA // config.TAMANHO_TILE + 2,
    )
    end_y = min(
        mapa_obj.altura,
        start_y + config.ALTURA_TELA // config.TAMANHO_TILE + 2,
    )
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            tile = mapa_obj.obter_tile(x, y)
            if tile and mapa_obj.is_blocked_terrain(x, y):
                screen_x = x * tile_size - cam_x
                screen_y = y * tile_size - cam_y
                
                if -tile_size < screen_x < config.LARGURA_TELA and -tile_size < screen_y < config.ALTURA_TELA:
                    surface.blit(blocked_overlay, (screen_x, screen_y))
                    pygame.draw.rect(
                        surface,
                        (255, 0, 0),
                        (screen_x, screen_y, tile_size, tile_size),
                        1,
                    )

    # 2. Desenha Hitboxes das Entidades (Verde/Azul)
    for ent in mapa_obj.entidades:
        rect = ent.hitbox.copy()
        rect.x -= cam_x
        rect.y -= cam_y
        
        cor = (0, 255, 0) if ent is mapa_obj.jogador else (0, 0, 255)
        pygame.draw.rect(surface, cor, rect, 1)

    # 3. Hitboxes dos projéteis (ciano). O ponto amarelo marca o centro.
    for projectile in mapa_obj.projeteis:
        if not projectile.active:
            continue
        rect = projectile._rect_at(projectile.x, projectile.y)
        rect.x -= cam_x
        rect.y -= cam_y
        pygame.draw.rect(surface, (0, 255, 255), rect, 1)
        pygame.draw.circle(surface, (255, 255, 0), rect.center, 2)

    # --- 4. Desenha Divisão de Chunks (Amarelo) ---
    # Calcula o tamanho de um chunk em pixels
    settings = getattr(mapa_obj, "settings", None)
    chunk_size = settings.chunk_size if settings else config.TAMANHO_CHUNK
    chunks_x = settings.chunks_x if settings else config.CHUNKS_X
    chunks_y = settings.chunks_y if settings else config.CHUNKS_Y
    pixel_chunk = chunk_size * config.TAMANHO_TILE
    
    # Linhas Verticais
    for cx in range(chunks_x + 1):
        x_world = cx * pixel_chunk
        x_screen = x_world - cam_x
        # Desenha uma linha de cima a baixo na tela
        pygame.draw.line(surface, (255, 255, 0), (x_screen, 0), (x_screen, config.ALTURA_TELA), 3)

    # Linhas Horizontais
    for cy in range(chunks_y + 1):
        y_world = cy * pixel_chunk
        y_screen = y_world - cam_y
        # Desenha uma linha da esquerda a direita na tela
        pygame.draw.line(surface, (255, 255, 0), (0, y_screen), (config.LARGURA_TELA, y_screen), 3)

    font = pygame.font.Font(None, 25)
    label = font.render("DEBUG HITBOXES [F3]", True, (255, 255, 255))
    background = label.get_rect(topleft=(12, 12)).inflate(12, 8)
    pygame.draw.rect(surface, (15, 15, 20), background)
    pygame.draw.rect(surface, (0, 255, 170), background, 2)
    surface.blit(label, (18, 16))
