import random
from perlin_noise import PerlinNoise 
from graphics import config
from entities import actor
from graphics import efeitos
from .grid import Grid
from . import biomas

# Configurações do Gerador

NOISE_SCALE = 40.0 
NOISE_OCTAVES = 4 

# --- NOVA CONFIGURAÇÃO ---
# Escala maior = Biomas maiores e mais largos
# Escala menor = Biomas mudam mais rápido
BIOME_SCALE = 80.0

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
            # Bloqueia se for parede, água ou se já tiver árvore (bloqueado=True)
            return tile.bloqueado or tile.tipo == "parede" or tile.tipo == "azul" or tile.tipo == "blue_ground"
        return True

    def gerar_novo_nivel(self):
        # ... (Limpezas iniciais iguais) ...
        
        self.seed = random.randint(0, 10000)
        print(f"Gerando mapa com Seed: {self.seed}")

        # 1. Ruído de Terreno (Define Água vs Terra)
        noise_gen = PerlinNoise(octaves=NOISE_OCTAVES, seed=self.seed)
        
        # 2. NOVO: Ruído de Bioma (Define Floresta vs Ruínas)
        # Usamos seed + 1 para que o desenho do bioma não seja igual ao da água
        biome_gen = PerlinNoise(octaves=2, seed=self.seed + 1)

        # --- PASSO 1: TERRENO E DECORAÇÃO ---
        for y in range(self.altura):
            for x in range(self.largura):
                tile = self.obter_tile(x, y)
                if not tile: continue

                # Valor de altura (Água/Terra)
                valor_ruido = noise_gen([x / NOISE_SCALE, y / NOISE_SCALE])
                
                # NOVO: Valor de "Temperatura/Bioma"
                valor_bioma = biome_gen([x / BIOME_SCALE, y / BIOME_SCALE])
                
                rng = random.randint(0, 100)

                # --- CAMADA 1, 2 e 3 (ÁGUA) ---
                if valor_ruido < -0.25:
                    tile.tipo = "deep_water"
                    tile.bloqueado = True
                elif valor_ruido < -0.15: 
                    biomas.aplicar_bioma_azul(self, x, y, tile, rng)
                elif valor_ruido < -0.08:
                    tile.tipo = "sand"
                    tile.bloqueado = False

                # --- CAMADA 4: TERRA FIRME ---
                else:
                    # --- AQUI ENTRA O SEU CÓDIGO ---
                    # Substitui o antigo "if random.random() < 0.8:"
                    
                    if valor_bioma < 0.0:
                        # Certeza que é Floresta densa
                        biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                    elif valor_bioma > 0.2:
                        # Certeza que é Ruína densa
                        biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)
                    else:
                        # Zona de Transição (Mistura)
                        if random.random() < 0.5:
                            biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                        else:
                            biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)

        # --- PASSO 2: SPAWN DE INIMIGOS (NOVO) ---
        # Tentamos spawnar monstros em lugares aleatórios válidos
        quantidade_monstros = 40  # Quantos bichos você quer no mapa?
        
        count = 0
        tentativas = 0
        while count < quantidade_monstros and tentativas < 1000:
            tentativas += 1
            mx = random.randint(5, self.largura - 5)
            my = random.randint(5, self.altura - 5)
            
            # Só spawna se o chão estiver livre (sem água, parede ou árvore)
            if not self.is_blocked_terrain(mx, my):
                
                # Sorteio do tipo de inimigo (Nível de dificuldade)
                rng_mob = random.random()
                if rng_mob < 0.6:   # 60% chance de Orc
                    nome, hp, dano, xp = "Orc", 30, 5, 15
                elif rng_mob < 0.9: # 30% chance de Troll
                    nome, hp, dano, xp = "Troll", 80, 15, 50
                else:               # 10% chance de Rei Troll
                    nome, hp, dano, xp = "REI TROLL", 150, 20, 100
                
                inimigo = actor.Entidade(mx, my, nome, hp, dano, xp_reward=xp)
                self.entidades.append(inimigo)
                count += 1

        # --- PASSO 3: SPAWN DO JOGADOR ---
        sx, sy = 15, 15
        encontrou_lugar = False
        for _ in range(100):
            tx = random.randint(10, self.largura - 10)
            ty = random.randint(10, self.altura - 10)
            if not self.is_blocked_terrain(tx, ty):
                sx, sy = tx, ty
                encontrou_lugar = True
                break
        
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
        # Update normal (IA, Física, Morte)
        for ent in self.entidades[:]:
            ent.update_ia(self)
            ent.update(self)
            if ent.hp <= 0:
                if ent != self.jogador:
                    self.jogador.ganhar_xp(ent.xp_reward)
                    self.entidades.remove(ent)
        
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