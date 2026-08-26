import pygame

def aplicar_flash_branco(surface):
    """ Cria um efeito de brilho branco (usado quando toma dano) """
    if not surface: return None
    mask = pygame.mask.from_surface(surface)
    flash_surf = mask.to_surface(setcolor=(255, 255, 255, 255), unsetcolor=(0, 0, 0, 0))
    return flash_surf

def gerar_vignette(largura, altura):
    """Create a subtle edge vignette while keeping the center fully clear."""
    vignette = pygame.Surface((largura, altura), pygame.SRCALPHA)
    steps = 12
    band = 12
    for step in range(steps):
        margin = step * band
        alpha = max(1, int(18 * (1 - step / steps)))
        rect = pygame.Rect(margin, margin, largura - margin * 2, altura - margin * 2)
        if rect.width > 0 and rect.height > 0:
            pygame.draw.rect(vignette, (0, 0, 0, alpha), rect, band)
    return vignette

def shader_ambientacao(bioma):
    if bioma == "ruinas":
        return (50, 20, 0, 40)
    elif bioma == "floresta":
        return (0, 30, 0, 20)
    return None
