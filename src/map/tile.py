class Tile:
    def __init__(self, tipo="grama", z_level=0, bloqueado=False):
        self.tipo = tipo 
        self.bloqueado = bloqueado
        self.altura = 0.0
        self.decoracao = None
        self.bioma = None
        self.orientacao = None
