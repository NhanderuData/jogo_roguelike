# src/debug.py
import pygame

def desenhar_hitboxes(surface, camera, mapa_obj, config):
    """
    Desenha apenas as hitboxes das entidades para evitar erros de atributo.
    """
    cam_x, cam_y = camera.camera_x, camera.camera_y
    tamanho = config.TAMANHO_TILE

    # Focamos apenas nas entidades por enquanto
    for ent in mapa_obj.entidades:
        # Pega a hitbox real da entidade e subtrai a câmera
        rect_debug = ent.hitbox.copy()
        rect_debug.x -= cam_x
        rect_debug.y -= cam_y
        
        # Cores: Verde (Heroi), Vermelho (Inimigos)
        cor = (0, 255, 0) if ent.nome == "Heroi" else (255, 50, 50)
        
        # Desenha a borda do retângulo
        pygame.draw.rect(surface, cor, rect_debug, 1)
        
        # Desenha o ponto central real para conferir o pivô
        centro_x = (ent.x * tamanho + tamanho // 2) - cam_x
        centro_y = (ent.y * tamanho + tamanho // 2) - cam_y
        pygame.draw.circle(surface, cor, (int(centro_x), int(centro_y)), 2)