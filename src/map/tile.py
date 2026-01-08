class Tile:
    def __init__(self, tipo="grama", z_level=0, bloqueado=False):
        self.tipo = tipo        # "grama", "terra", "parede"
        self.bloqueado = bloqueado
        
    