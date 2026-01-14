import random
from perlin_noise import PerlinNoise 
from core import config
from entities import actor
from graphics import efeitos
from .grid import Grid
from . import biomas
# Novos imports necessários
from entities.loot import LootDrop
from core.game_data import DATA_INIMIGOS

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
        self.items_no_chao = [] # Lista para os drops
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
        self.items_no_chao = []
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

                # Reseta o tile
                tile.bloqueado = False
                tile.tipo = "terra"

                # Calcula valores de ruído para esta coordenada
                valor_ruido = noise_gen([x / NOISE_SCALE, y / NOISE_SCALE])
                valor_bioma = biome_gen([x / BIOME_SCALE, y / BIOME_SCALE])
                rng = random.randint(0, 100)

                # --- LÓGICA DE TERRENO ---
                if valor_ruido < -0.25:
                    tile.tipo = "deep_water"
                    tile.bloqueado = True
                elif valor_ruido < -0.15: 
                    biomas.aplicar_bioma_azul(self, x, y, tile, rng)
                elif valor_ruido < -0.08:
                    tile.tipo = "sand"
                    tile.bloqueado = False 
                else:
                    # --- LÓGICA DE BIOMAS ---
                    if valor_bioma < 0.0: # Floresta
                        biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                    elif valor_bioma > 0.2: # Ruínas
                        biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)
                    else: # Transição
                        if random.random() < 0.5:
                            biomas.aplicar_bioma_floresta(self, x, y, tile, rng)
                        else:
                            biomas.aplicar_bioma_ruinas(self, x, y, tile, rng)

        # 4. Spawn do Jogador
        sx, sy = 15, 15
        encontrou = False
        for _ in range(100):
            tx = random.randint(5, self.largura - 5)
            ty = random.randint(5, self.altura - 5)
            if not self.is_blocked_terrain(tx, ty):
                sx, sy = tx, ty
                encontrou = True
                break
        
        if not encontrou:
            tile = self.obter_tile(sx, sy)
            if tile: 
                tile.tipo = "terra"
                tile.bloqueado = False

        if not self.jogador:
            # Jogador agora é "Survivor" conforme o contexto zumbi
            self.jogador = actor.Entidade(sx, sy, "Survivor")
        else:
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
            self.jogador.physics.moving = False
        
        self.entidades.append(self.jogador)

        # 5. Spawn de Inimigos (Walker, Runner, Tank)
        quantidade_monstros = 40
        count = 0
        tentativas = 0
        while count < quantidade_monstros and tentativas < 2000:
            tentativas += 1
            mx = random.randint(5, self.largura - 5)
            my = random.randint(5, self.altura - 5)
            
            dist = ((mx - sx)**2 + (my - sy)**2)**0.5
            if dist < 10: continue

            if not self.is_blocked_terrain(mx, my):
                # Recalcula o bioma neste ponto para saber qual zumbi spawnar
                v_ruido = noise_gen([mx / NOISE_SCALE, my / NOISE_SCALE])
                v_bioma = biome_gen([mx / BIOME_SCALE, my / BIOME_SCALE])
                
                # Determina o tipo de bioma local
                tipo_bioma = "padrao"
                if v_ruido < -0.15 and v_ruido >= -0.25:
                    tipo_bioma = "azul"
                elif v_bioma > 0.2:
                    tipo_bioma = "ruinas"
                
                # --- Seleção do Inimigo (Sua lógica corrigida) ---
                if tipo_bioma == "ruinas":
                    nome = "Runner"
                elif tipo_bioma == "azul": 
                    nome = "Tank"
                else:
                    nome = "Walker"
                
                inimigo = actor.Entidade(mx, my, nome)
                self.entidades.append(inimigo)
                count += 1

    def update(self):
        # Atualiza Jogador
        if self.jogador:
            self.jogador.update(self)
            
        # Atualiza Inimigos
        for ent in self.entidades:
            if ent != self.jogador:
                ent.update(self)

        # --- LÓGICA DE MORTE E LOOT (Unificada) ---
        for ent in self.entidades[:]:
            if ent.hp <= 0:
                if ent != self.jogador:
                    # 1. Desbloqueia tile (árvores/estruturas)
                    tx, ty = int(round(ent.x)), int(round(ent.y))
                    tile_atual = self.obter_tile(tx, ty)
                    if tile_atual: 
                        tile_atual.bloqueado = False
                        # print(f"Objeto destruído em {tx},{ty}") 
                    
                    # 2. SISTEMA DE LOOT
                    # Pega dados do dicionário para ver se dropa algo
                    dados = DATA_INIMIGOS.get(ent.nome)
                    if dados and "loot" in dados:
                        chance = dados.get("chance_loot", 0.0)
                        if random.random() < chance:
                            item_escolhido = random.choice(dados["loot"])
                            
                            # Cria o Drop na posição da entidade morta
                            drop = LootDrop(ent.x, ent.y, item_escolhido)
                            self.items_no_chao.append(drop)
                            print(f"Loot Dropado: {item_escolhido}")

                    # 3. XP e Remoção
                    self.jogador.ganhar_xp(ent.xp_reward)
                    if ent in self.entidades:
                        self.entidades.remove(ent)
                    
        
        # Atualiza Projéteis
        for p in self.projeteis[:]:
            p.update(self)
            if not p.active: self.projeteis.remove(p)
            
        # Atualiza Efeitos
        for e in self.efeitos[:]:
            e.update()
            if e.life <= 0: self.efeitos.remove(e)
            
        # Atualiza Textos Flutuantes
        for t in self.textos[:]:
            t.update()
            if t.life <= 0: self.textos.remove(t)

        # Atualiza Animação dos Itens no Chão
        for loot in self.items_no_chao:
            loot.update(0.1)

    # Função corrigida para aceitar Texto (str) e Cores personalizadas
    def criar_texto_dano(self, x, y, valor, cor=(255, 50, 50)):
        txt = efeitos.TextoFlutuante(x, y, str(valor), cor)
        self.textos.append(txt)