# src/debug.py
import pygame

def desenhar_hitboxes(surface, camera, mapa_obj, config):
    # 1. Desenha Tiles Bloqueados (Onde o jogador não pode pisar)
    # Isso vai mostrar quadrados vermelhos semi-transparentes em paredes e árvores
    for y in range(mapa_obj.altura):
        for x in range(mapa_obj.largura):
            tile = mapa_obj.obter_tile(x, y)
            if tile and tile.bloqueado:
                screen_x = x * config.TAMANHO_TILE - camera.camera_x
                screen_y = y * config.TAMANHO_TILE - camera.camera_y
                
                # Só desenha se estiver na tela
                if -32 < screen_x < config.LARGURA_TELA and -32 < screen_y < config.ALTURA_TELA:
                    s = pygame.Surface((32, 32), pygame.SRCALPHA)
                    s.fill((255, 0, 0, 100)) # Vermelho transparente
                    surface.blit(s, (screen_x, screen_y))
                    pygame.draw.rect(surface, (255, 0, 0), (screen_x, screen_y, 32, 32), 1)

    # 2. Desenha as hitboxes das Entidades (Verde/Azul)
    for ent in mapa_obj.entidades:
        rect = ent.hitbox.copy()
        rect.x -= camera.camera_x
        rect.y -= camera.camera_y
        
        cor = (0, 255, 0) if ent.nome == "Heroi" else (0, 0, 255)
        pygame.draw.rect(surface, cor, rect, 1)