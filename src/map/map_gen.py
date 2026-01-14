import random
from perlin_noise import PerlinNoise 
from core import config
from entities import actor
from graphics import efeitos
from .grid import Grid
from . import biomas

# Configurações do Gerador
NOISE_SCALE = 40.0 
NOISE_OCTAVES = 2 
BIOME_SCALE = 120.0

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
            # Bloqueia se for parede, água profunda ou se o tile estiver marcado como bloqueado (árvores)
            return tile.bloqueado or tile.tipo == "parede" or tile.tipo == "deep_water"
        return True

    def gerar_novo_nivel(self):
        # 1. Reset das Listas
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        
        self.seed = random.randint(0, 10000)
        print(f"Gerando Mapa Aberto (Seed: {self.seed})")

        # 2. Preparar Geradores de Ruído
        noise_gen = PerlinNoise(octaves=NOISE_OCTAVES, seed=self.seed)
        biome_gen = PerlinNoise(octaves=2, seed=self.seed + 1)

        # 3. Gerar o Terreno (Loop por todo o mapa)
        for y in range(self.altura):
            for x in range(self.largura):
                tile = self.obter_tile(x, y)
                if not tile: continue

                # Reseta o tile para o padrão antes de aplicar bioma
                tile.bloqueado = False
                tile.tipo = "terra"

                # Calcula valores de ruído para esta coordenada
                valor_ruido = noise_gen([x / NOISE_SCALE, y / NOISE_SCALE])
                valor_bioma = biome_gen([x / BIOME_SCALE, y / BIOME_SCALE])
                rng = random.randint(0, 100)

                # --- LÓGICA DE TERRENO (Água vs Terra) ---
                if valor_ruido < -0.25:
                    tile.tipo = "deep_water"
                    tile.bloqueado = True
                elif valor_ruido < -0.15: 
                    biomas.aplicar_bioma_azul(self, x, y, tile, rng)
                elif valor_ruido < -0.08:
                    tile.tipo = "sand"
                    tile.bloqueado = False # Areia é caminhável

                # --- LÓGICA DE BIOMAS (Floresta vs Ruínas) ---
                else:
                    if valor_bioma < 0.0:
                        # Floresta
                        biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                    elif valor_bioma > 0.2:
                        # Ruínas
                        biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)
                    else:
                        # Zona de Transição (Mistura os dois)
                        if random.random() < 0.5:
                            biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                        else:
                            biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)

        # 4. Spawn do Jogador (Busca lugar seguro)
        sx, sy = 15, 15
        encontrou = False
        # Tenta 100 vezes achar um lugar que não seja água ou parede
        for _ in range(100):
            tx = random.randint(5, self.largura - 5)
            ty = random.randint(5, self.altura - 5)
            if not self.is_blocked_terrain(tx, ty):
                sx, sy = tx, ty
                encontrou = True
                break
        
        # Se não achou, força o chão na posição padrão
        if not encontrou:
            tile = self.obter_tile(sx, sy)
            if tile: 
                tile.tipo = "terra"
                tile.bloqueado = False

        # --- REFATORADO: Criação do Jogador (Sem status hardcoded) ---
        if not self.jogador:
            # Passamos apenas o nome "Heroi". A classe Entidade puxa HP/Dano do game_data.py
            self.jogador = actor.Entidade(sx, sy, "Heroi")
        else:
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            # Reseta HP baseado no máximo atual (que veio do componente de combate)
            self.jogador.hp = self.jogador.hp_max
            self.jogador.physics.moving = False
        
        self.entidades.append(self.jogador)

        # 5. Spawn de Inimigos (Espalhados pelo mapa)
        quantidade_monstros = 40
        count = 0
        tentativas = 0
        while count < quantidade_monstros and tentativas < 2000:
            tentativas += 1
            mx = random.randint(5, self.largura - 5)
            my = random.randint(5, self.altura - 5)
            
            # Não spawna muito perto do jogador
            dist = ((mx - sx)**2 + (my - sy)**2)**0.5
            if dist < 10: continue

            if not self.is_blocked_terrain(mx, my):
                rng_mob = random.random()
                
                # --- REFATORADO: Seleção de Nome Apenas ---
                nome = "Orc" # Padrão
                
                if rng_mob < 0.6:   
                    nome = "Orc"
                elif rng_mob < 0.9: 
                    nome = "Troll"
                else:               
                    nome = "REI TROLL"
                
                # Cria a entidade passando apenas o nome!
                # Os atributos (HP, Dano, XP) são configurados automaticamente dentro de actor.py
                inimigo = actor.Entidade(mx, my, nome)
                self.entidades.append(inimigo)
                count += 1

    def update(self):
        # Atualiza Jogador
        if self.jogador:
            self.jogador.update(self)
            
        # Atualiza Entidades (Inimigos)
        for ent in self.entidades:
            if ent != self.jogador:
                ent.update(self)

        # Verifica mortes
        for ent in self.entidades[:]:
            if ent.hp <= 0:
                if ent != self.jogador:
                    # --- CORREÇÃO ROBUSTA ---
                    # Usa round() para garantir que pegamos o tile mais próximo (10.0 ou 9.9 viram 10)
                    # e não int() que cortaria 9.9 para 9.
                    tx = int(round(ent.x))
                    ty = int(round(ent.y))
                    
                    tile_atual = self.obter_tile(tx, ty)
                    if tile_atual:
                        tile_atual.bloqueado = False
                        print(f"DEBUG: Árvore morta em {tx},{ty}. Tile desbloqueado!") # Log para conferir
                    # ------------------------
                    
                    self.jogador.ganhar_xp(ent.xp_reward)
                    self.entidades.remove(ent)
                    
        
        # Atualiza Projéteis
        for p in self.projeteis[:]:
            p.update(self)
            if not p.active: self.projeteis.remove(p)
            
        # Atualiza Efeitos
        for e in self.efeitos[:]:
            e.update()
            if e.life <= 0: self.efeitos.remove(e)
            
        # Atualiza Textos
        for t in self.textos[:]:
            t.update()
            if t.life <= 0: self.textos.remove(t)

    def criar_texto_dano(self, x, y, valor):
        cor = (255, 50, 50)
        txt = efeitos.TextoFlutuante(x, y, str(int(valor)), cor)
        self.textos.append(txt)