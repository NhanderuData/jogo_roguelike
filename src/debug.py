# src/debug.py
import pygame

def desenhar_hitboxes(surface, camera, mapa_obj, config):
    # 1. Desenha Tiles Bloqueados (Vermelho)
    for y in range(mapa_obj.altura):
        for x in range(mapa_obj.largura):
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

    # --- NOVO: 3. Desenha Divisão de Chunks (Amarelo) ---
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