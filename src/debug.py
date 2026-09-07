# src/debug.py
import pygame

def desenhar_hitboxes(surface, camera, mapa_obj, config):
    # 1. Desenha Tiles Bloqueados (Vermelho)
    start_x = max(0, int(camera.camera_x // config.TAMANHO_TILE))
    start_y = max(0, int(camera.camera_y // config.TAMANHO_TILE))
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
            if tile and tile.bloqueado:
                screen_x = x * config.TAMANHO_TILE - camera.camera_x
                screen_y = y * config.TAMANHO_TILE - camera.camera_y
                
                if -32 < screen_x < config.LARGURA_TELA and -32 < screen_y < config.ALTURA_TELA:
                    s = pygame.Surface((32, 32), pygame.SRCALPHA)
                    s.fill((255, 0, 0, 100)) 
                    surface.blit(s, (screen_x, screen_y))
                    pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_y, 32, 32), 1)

    # 2. Desenha Hitboxes das Entidades (Verde/Azul)
    for ent in mapa_obj.entidades:
        rect = ent.hitbox.copy()
        rect.x -= camera.camera_x
        rect.y -= camera.camera_y
        
        cor = (0, 255, 0) if ent.nome == "Heroi" or ent.nome == "Survivor" else (0, 0, 255)
        pygame.draw.rect(surface, cor, rect, 1)

    # 3. Hitboxes dos projéteis (ciano). O ponto amarelo marca o centro.
    for projectile in mapa_obj.projeteis:
        if not projectile.active:
            continue
        rect = projectile._rect_at(projectile.x, projectile.y)
        rect.x -= camera.camera_x
        rect.y -= camera.camera_y
        pygame.draw.rect(surface, (0, 255, 255), rect, 1)
        pygame.draw.circle(surface, (255, 255, 0), rect.center, 2)

    # --- 4. Desenha Divisão de Chunks (Amarelo) ---
    # Calcula o tamanho de um chunk em pixels
    pixel_chunk = config.TAMANHO_CHUNK * config.TAMANHO_TILE
    
    # Linhas Verticais
    for cx in range(config.CHUNKS_X + 1):
        x_world = cx * pixel_chunk
        x_screen = x_world - camera.camera_x
        # Desenha uma linha de cima a baixo na tela
        pygame.draw.line(surface, (255, 255, 0), (x_screen, 0), (x_screen, config.ALTURA_TELA), 3)

    # Linhas Horizontais
    for cy in range(config.CHUNKS_Y + 1):
        y_world = cy * pixel_chunk
        y_screen = y_world - camera.camera_y
        # Desenha uma linha da esquerda a direita na tela
        pygame.draw.line(surface, (255, 255, 0), (0, y_screen), (config.LARGURA_TELA, y_screen), 3)

    font = pygame.font.Font(None, 25)
    label = font.render("DEBUG HITBOXES [F3]", True, (255, 255, 255))
    background = label.get_rect(topleft=(12, 12)).inflate(12, 8)
    pygame.draw.rect(surface, (15, 15, 20), background)
    pygame.draw.rect(surface, (0, 255, 170), background, 2)
    surface.blit(label, (18, 16))
