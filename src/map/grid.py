# src/map/grid.py
from .tile import Tile

class Grid:
    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        # Removemos o '0' do construtor
        self.tiles = [[Tile("grama") for _ in range(largura)] for _ in range(altura)]

    def configurar_tile(self, x, y, tipo, bloqueado=False):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            self.tiles[y][x] = Tile(tipo=tipo, bloqueado=bloqueado)

    def obter_tile(self, x, y):
        ix, iy = int(x), int(y)
        if 0 <= ix < self.largura and 0 <= iy < self.altura:
            return self.tiles[iy][ix]
        return None
