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
    surf_w = surface.get_width()
    surf_h = surface.get_height()

    # 1. Desenha Tiles Bloqueados (Vermelho)
    start_x = max(0, int(cam_x // tile_size))
    start_y = max(0, int(cam_y // tile_size))
    end_x = min(
        mapa_obj.largura,
        start_x + surf_w // tile_size + 2,
    )
    end_y = min(
        mapa_obj.altura,
        start_y + surf_h // tile_size + 2,
    )
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            tile = mapa_obj.obter_tile(x, y)
            if tile and mapa_obj.is_blocked_terrain(x, y):
                tile_hb = (
                    mapa_obj.get_tile_hitbox(x, y)
                    if hasattr(mapa_obj, "get_tile_hitbox")
                    else None
                )
                if tile_hb:
                    screen_rect = pygame.Rect(
                        tile_hb.x - cam_x,
                        tile_hb.y - cam_y,
                        tile_hb.width,
                        tile_hb.height,
                    )
                    if screen_rect.colliderect(surface.get_rect()):
                        sub_overlay = pygame.Surface(
                            (screen_rect.width, screen_rect.height),
                            pygame.SRCALPHA,
                        )
                        sub_overlay.fill((255, 0, 0, 100))
                        surface.blit(sub_overlay, screen_rect.topleft)
                        pygame.draw.rect(surface, (255, 0, 0), screen_rect, 1)
                else:
                    screen_x = x * tile_size - cam_x
                    screen_y = y * tile_size - cam_y
                    
                    if -tile_size < screen_x < surf_w and -tile_size < screen_y < surf_h:
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
    settings = getattr(mapa_obj, "settings", None)
    chunk_size = settings.chunk_size if settings else config.TAMANHO_CHUNK
    chunks_x = settings.chunks_x if settings else config.CHUNKS_X
    chunks_y = settings.chunks_y if settings else config.CHUNKS_Y
    pixel_chunk = chunk_size * config.TAMANHO_TILE
    
    # Linhas Verticais
    for cx in range(chunks_x + 1):
        x_world = cx * pixel_chunk
        x_screen = x_world - cam_x
        pygame.draw.line(surface, (255, 255, 0), (x_screen, 0), (x_screen, surf_h), 2)

    # Linhas Horizontais
    for cy in range(chunks_y + 1):
        y_world = cy * pixel_chunk
        y_screen = y_world - cam_y
        pygame.draw.line(surface, (255, 255, 0), (0, y_screen), (surf_w, y_screen), 2)


def desenhar_hud_f3(surface, camera):
    """Renderiza a caixa de status do modo debug e controle de zoom da câmera."""
    zoom = getattr(camera, "zoom", 1.0)
    font = pygame.font.Font(None, 24)
    font_sub = pygame.font.Font(None, 19)

    text_title = f"DEBUG [F3] | ZOOM DA CÂMERA: {zoom:.2f}x"
    text_hint = "Scroll Mouse: Expandir / Aproximar | Clique do Meio: Reset (1.0x)"

    surf_title = font.render(text_title, True, (0, 255, 180))
    surf_hint = font_sub.render(text_hint, True, (220, 220, 230))

    box_w = max(surf_title.get_width(), surf_hint.get_width()) + 20
    box_h = surf_title.get_height() + surf_hint.get_height() + 14

    bg_rect = pygame.Rect(12, 12, box_w, box_h)
    panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    panel.fill((15, 18, 24, 220))
    surface.blit(panel, (12, 12))
    pygame.draw.rect(surface, (0, 255, 180), bg_rect, 2, border_radius=4)

    surface.blit(surf_title, (22, 18))
    surface.blit(surf_hint, (22, 18 + surf_title.get_height() + 2))
