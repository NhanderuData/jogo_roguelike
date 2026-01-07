class Tile:
    def __init__(self, tipo="grama", z_level=0, bloqueado=False):
        self.tipo = tipo        # "grama", "terra", "parede"
        self.z_level = z_level  # 0: base, 1: degrau, 2: montanha
        self.bloqueado = bloqueado
        
    def get_offset_y(self):
        """ Retorna o quanto o desenho 'sobe' no eixo Y visual """
        return self.z_level * 12