# src/map/tile.py

class Tile:
    def __init__(self, tipo="grama", z_level=0, bloqueado=False):
        self.tipo = tipo        # "grama", "terra", "pedra"
        self.z_level = z_level  # 0: chao, 1: elevado, 2: muito elevado
        self.bloqueado = bloqueado
        
    def get_offset_y(self):
        """ Retorna o deslocamento em pixels para o efeito visual de altura """
        return self.z_level * 12  # Sobe 12 pixels por nível de altura