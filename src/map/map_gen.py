import random
from graphics import config
from entities import actor
from graphics import efeitos
from .grid import Grid

from . import biomas

class Mapa:
    def __init__(self):
        self.largura = config.LARGURA_MAPA
        self.altura = config.ALTURA_MAPA
        self.grid_sistema = Grid(self.largura, self.altura)
        self.grid = self.grid_sistema.tiles
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        self.jogador = None
        self.gerar_novo_nivel()

    def obter_tile(self, x, y):
        return self.grid_sistema.obter_tile(x, y)

    def is_blocked_terrain(self, x, y):
        tile = self.obter_tile(x, y)
        if tile:
            return tile.bloqueado or tile.tipo == "parede"
        return True

    def gerar_novo_nivel(self):
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        
        # Spawn do Herói
        sx, sy = 15, 15
        if not self.jogador: 
            self.jogador = actor.Entidade(sx, sy, "Heroi", 100, 10, xp_reward=0)
        else: 
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
        self.entidades.append(self.jogador)
        
        # Gera o terreno por Chunks
        for y in range(config.CHUNKS_Y):
            for x in range(config.CHUNKS_X):
                self.gerar_chunk(x * config.TAMANHO_CHUNK, y * config.TAMANHO_CHUNK)

    def gerar_chunk(self, ox, oy):
        # 1. Escolhe o bioma para este chunk específico
        tipo_bioma = random.choice(["floresta", "ruinas"])
        tem_elevacao = random.random() < 0.4 

        for y in range(config.TAMANHO_CHUNK):
            for x in range(config.TAMANHO_CHUNK):
                gx, gy = ox + x, oy + y
                if gx >= self.largura or gy >= self.altura: continue
                
                tile = self.obter_tile(gx, gy)
                
                # 2. Aplica elevação básica (pode ser modificada pelo bioma depois)
                if tem_elevacao and 8 < x < 22 and 8 < y < 22:
                    tile.z_leavel = 1
                    tile.tipo = "terra"

                # 3. CHAMA A LÓGICA DO BIOMA (Usa as funções do biomas.py)
                rng = random.randint(0, 100)
                if tipo_bioma == "floresta":
                    biomas.aplicar_bioma_floresta(self, gx, gy, tile, rng)
                else:
                    biomas.aplicar_bioma_ruinas(self, gx, gy, tile, rng)

        # 4. SPAWN DE INIMIGOS DO BIOMA (Usa a função do biomas.py)
        biomas.spawn_inimigos_por_bioma(self, ox, oy, tipo_bioma)

    def update(self):
        for ent in self.entidades[:]:
            # 1. IA Roda Primeiro (Decide para onde vai)
            ent.update_ia(self)

            # 2. Atualização Física Roda Depois (Move e ajusta Hitbox)
            # O erro estava aqui: agora passamos 'self' (o objeto mapa)
            ent.update(self) 

            if ent.hp <= 0:
                if ent != self.jogador:
                    self.jogador.ganhar_xp(ent.xp_reward)
                    self.entidades.remove(ent)
        
        # ... (o resto do código de projéteis e efeitos continua igual) ...
        for p in self.projeteis[:]:
            p.update(self)
            if not p.active: self.projeteis.remove(p)
            
        for e in self.efeitos[:]:
            e.update()
            if e.life <= 0: self.efeitos.remove(e)

        for t in self.textos[:]:
            t.update()
            if t.vida <= 0: self.textos.remove(t)

    def criar_texto_dano(self, x, y, valor):
        cor = (255, 50, 50) 
        txt = efeitos.TextoFlutuante(x, y, str(int(valor)), cor)
        self.textos.append(txt)