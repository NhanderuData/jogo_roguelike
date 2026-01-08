# src/debug.py
import pygame

def desenhar_hitboxes(surface, camera, mapa_obj, config):
    # Desenha as hitboxes das Entidades
    for ent in mapa_obj.entidades:
        # Copia o retângulo original (que está em coordenadas do MUNDO)
        rect = ent.hitbox.copy()
        
        # Subtrai a câmera para converter para coordenadas da TELA
        rect.x -= camera.camera_x
        rect.y -= camera.camera_y
        
        # Desenha: Verde para Jogador, Vermelho para Inimigos
        cor = (0, 255, 0) if ent.nome == "Heroi" else (255, 0, 0)
        pygame.draw.rect(surface, cor, rect, 1)

    # (Opcional) Desenha o ponto central (pés) para conferência
    p = mapa_obj.jogador
    if p:
        screen_x = p.x * config.TAMANHO_TILE - camera.camera_x
        screen_y = p.y * config.TAMANHO_TILE - camera.camera_y
        
        # Ponto exato onde o jogo acha que o X/Y está (centro do tile)
        cx = screen_x + (config.TAMANHO_TILE // 2)
        cy = screen_y + (config.TAMANHO_TILE // 2)
        
        pygame.draw.circle(surface, (255, 255, 0), (int(cx), int(cy)), 2)