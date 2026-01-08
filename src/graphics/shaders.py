import pygame

def aplicar_flash_branco(surface):
    """ Cria um efeito de brilho branco (usado quando toma dano) """
    if not surface: return None
    mask = pygame.mask.from_surface(surface)
    flash_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    return flash_surf

def gerar_vignette(largura, altura):
    """ Cria aquela borda escura que foca no centro da tela """
    vignette = pygame.Surface((largura, altura), pygame.SRCALPHA)
    # Desenha um degradê radial simulado
    for r in range(int(largura * 1.2), 0, -15):
        alpha = int(180 * (1 - r / largura)) # Escurece conforme se afasta do centro
        if alpha < 0: alpha = 0
        pygame.draw.circle(vignette, (0, 0, 0, alpha), (largura//2, altura//2), r)
    return vignette

def shader_ambientacao(bioma):
    if bioma == "ruinas":
        return (50, 20, 0, 40)
    elif bioma == "floresta":
        return (0, 30, 0, 20)
    return None