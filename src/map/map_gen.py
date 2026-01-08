import random
# MUDANÇA 1: Importamos a classe da biblioteca que você instalou
from perlin_noise import PerlinNoise 
from graphics import config
from entities import actor
from graphics import efeitos
from .grid import Grid
from . import biomas

# --- Configurações do Gerador ---
# SCALE: Controla o "Zoom". 
# Valores ALTOS (ex: 50.0) deixam os biomas maiores (zoom in).
# Valores BAIXOS (ex: 10.0) deixam tudo muito misturado (zoom out).
NOISE_SCALE = 40.0 
NOISE_OCTAVES = 4 # Detalhes do terreno

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
        
        self.seed = random.randint(0, 10000)
        self.gerar_novo_nivel()

    def obter_tile(self, x, y):
        return self.grid_sistema.obter_tile(x, y)

    def is_blocked_terrain(self, x, y):
        tile = self.obter_tile(x, y)
        if tile:
            # Bloqueia se for parede ou se for Água
            return tile.bloqueado or tile.tipo == "parede" or tile.tipo == "azul"
        return True

    def gerar_novo_nivel(self):
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        
        self.seed = random.randint(0, 10000)
        print(f"Gerando mapa com Seed: {self.seed}")

        # MUDANÇA 2: Cria o objeto gerador de ruído
        noise_gen = PerlinNoise(octaves=NOISE_OCTAVES, seed=self.seed)

        # Percorre cada tile do mapa
        for y in range(self.altura):
            for x in range(self.largura):
                tile = self.obter_tile(x, y)
                if not tile: continue

                # MUDANÇA 3: Chamada da função perlin-noise
                # Ela espera uma lista de coordenadas [x, y]. 
                # Dividimos pelo SCALE para fazer o "zoom" nas formas.
                valor_ruido = noise_gen([x / NOISE_SCALE, y / NOISE_SCALE])
                
                rng = random.randint(0, 100)

                # --- Definição dos Biomas ---
                # Ajuste os valores aqui se tiver muita ou pouca água.
                # O perlin-noise geralmente retorna valores entre -0.5 e 0.5 (ou -1 e 1)
                
                if valor_ruido < -0.15: 
                    # Nível do mar
                    biomas.aplicar_bioma_azul(self, x, y, tile, rng)
                else:
                    # Terra firme
                    # Usei um segundo valor aleatório simples para variar floresta/ruínas
                    if random.random() < 0.8:
                        biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                    else:
                        biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)

        # --- Spawn do Jogador Seguro ---
        # Procura um lugar que NÃO seja bloqueado (água/parede)
        sx, sy = 15, 15
        encontrou_lugar = False
        
        # Tenta 100 vezes achar um lugar aleatório seco
        for _ in range(100):
            tx = random.randint(2, self.largura - 2)
            ty = random.randint(2, self.altura - 2)
            if not self.is_blocked_terrain(tx, ty):
                sx, sy = tx, ty
                encontrou_lugar = True
                break
        
        # Se não achou (muito azar), força a posição inicial a virar terra
        if not encontrou_lugar:
            tile = self.obter_tile(sx, sy)
            if tile:
                tile.tipo = "terra"
                tile.bloqueado = False

        if not self.jogador:
            self.jogador = actor.Entidade(sx, sy, "Heroi", 100, 10, xp_reward=0)
        else:
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
        
        self.entidades.append(self.jogador)

    def update(self):
        # ... (O resto do código update continua igual) ...
        for ent in self.entidades[:]:
            ent.update_ia(self)
            ent.update(self)
            if ent.hp <= 0:
                if ent != self.jogador:
                    self.jogador.ganhar_xp(ent.xp_reward)
                    self.entidades.remove(ent)
        for p in self.projeteis[:]:
            p.update(self)
            if not p.active:
                self.projeteis.remove(p)
        for e in self.efeitos[:]:
            e.update()
            if e.life <= 0:
                self.efeitos.remove(e)
        for t in self.textos[:]:
            t.update()
            if t.vida <= 0:
                self.textos.remove(t)

    def criar_texto_dano(self, x, y, valor):
        cor = (255, 50, 50)
        txt = efeitos.TextoFlutuante(x, y, str(int(valor)), cor)
        self.textos.append(txt)