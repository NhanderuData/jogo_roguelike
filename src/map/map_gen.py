# src/map/map_gen.py
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

    def desenhar_faixa_estrada(self, x1, y1, x2, y2, largura_estrada=5):
        """ Desenha uma linha grossa entre dois pontos (Horizontal ou Vertical) """
        
        # Determina os limites (start/end)
        start_x, end_x = min(x1, x2), max(x1, x2)
        start_y, end_y = min(y1, y2), max(y1, y2)
        
        # Calcula o 'raio' da estrada (ex: 5 tiles = 2 pra cada lado + 1 centro)
        raio = largura_estrada // 2 

        # Loop apenas na área da estrada
        for y in range(start_y - raio, end_y + raio + 1):
            for x in range(start_x - raio, end_x + raio + 1):
                
                # Verificações de segurança
                if x < 0 or x >= self.largura or y < 0 or y >= self.altura:
                    continue
                
                tile = self.obter_tile(x, y)
                if tile:
                    tile.tipo = "estrada"
                    tile.bloqueado = False
                    
                    # Remove árvores/pedras que estejam no meio do asfalto
                    for ent in self.entidades[:]:
                        if int(ent.x) == x and int(ent.y) == y:
                            self.entidades.remove(ent)

    def gerar_estradas_walker(self):
        print("Gerando estradas contínuas (Walker)...")
        largura_chunk = config.TAMANHO_CHUNK
        chunks_x = config.CHUNKS_X
        chunks_y = config.CHUNKS_Y
        
        # Lista de conexões: armazena tuplas ((cx1, cy1), (cx2, cy2))
        # Isso garante que desenhamos apenas segmentos válidos
        conexoes = []
        chunks_visitados = []

        # 1. Ponto de partida (Borda Esquerda)
        cx, cy = 0, random.randint(0, chunks_y - 1)
        chunks_visitados.append((cx, cy))
        
        # 2. Caminhar até a Borda Direita (Estrada Principal)
        while cx < chunks_x - 1:
            opcoes = []
            
            # Prioridade: Direita (para cruzar o mapa)
            if cx + 1 < chunks_x: 
                opcoes.append((1, 0)) # Direita
                opcoes.append((1, 0)) # Peso maior
                opcoes.append((1, 0)) 
            
            # Cima
            if cy - 1 >= 0: opcoes.append((0, -1))
            
            # Baixo
            if cy + 1 < chunks_y: opcoes.append((0, 1))
            
            # Escolhe direção
            dx, dy = random.choice(opcoes)
            
            # Define o vizinho
            nx, ny = cx + dx, cy + dy
            
            # Registra a conexão
            conexoes.append(((cx, cy), (nx, ny)))
            chunks_visitados.append((nx, ny))
            
            # Move o walker
            cx, cy = nx, ny

        # 3. Ramificações (Branches)
        # Cria ruas secundárias a partir da estrada principal
        num_branches = 3
        for _ in range(num_branches):
            if not chunks_visitados: break
            
            # Começa de um ponto aleatório da estrada principal
            start_node = random.choice(chunks_visitados)
            bx, by = start_node
            
            # Anda alguns passos
            for _ in range(random.randint(1, 3)):
                dirs = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                dx, dy = random.choice(dirs)
                
                nx, ny = bx + dx, by + dy
                
                if 0 <= nx < chunks_x and 0 <= ny < chunks_y:
                    conexoes.append(((bx, by), (nx, ny)))
                    chunks_visitados.append((nx, ny)) # Adiciona para futuras ramificações
                    bx, by = nx, ny

        # 4. Desenhar o Asfalto
        # Itera sobre as conexões seguras e desenha linhas entre os centros
        for (c1, c2) in conexoes:
            # Converte Coordenada de Chunk -> Coordenada de Pixel (Centro)
            p1_x = c1[0] * largura_chunk + (largura_chunk // 2)
            p1_y = c1[1] * largura_chunk + (largura_chunk // 2)
            
            p2_x = c2[0] * largura_chunk + (largura_chunk // 2)
            p2_y = c2[1] * largura_chunk + (largura_chunk // 2)
            
            self.desenhar_faixa_estrada(p1_x, p1_y, p2_x, p2_y, largura_estrada=5)

    def is_blocked_terrain(self, x, y):
        tile = self.obter_tile(x, y)
        if tile:
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
        
        # --- 3.5 GERAR ESTRADAS (WALKER) ---
        self.gerar_estradas_walker()
        # -----------------------------------

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
            self.jogador = actor.Entidade(sx, sy, "Survivor")
        else:
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
            self.jogador.physics.moving = False
            self.jogador.physics.update_hitbox()
        
        self.entidades.append(self.jogador)

        # 5. Spawn de Inimigos
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
                v_ruido = noise_gen([mx / NOISE_SCALE, my / NOISE_SCALE])
                v_bioma = biome_gen([mx / BIOME_SCALE, my / BIOME_SCALE])
                
                tipo_bioma = "padrao"
                if v_ruido < -0.15 and v_ruido >= -0.25:
                    tipo_bioma = "azul"
                elif v_bioma > 0.2:
                    tipo_bioma = "ruinas"
                
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

        # --- LÓGICA DE MORTE E LOOT ---
        for ent in self.entidades[:]:
            if ent.hp <= 0:
                if ent != self.jogador:
                    tx, ty = int(round(ent.x)), int(round(ent.y))
                    tile_atual = self.obter_tile(tx, ty)
                    if tile_atual: 
                        tile_atual.bloqueado = False
                    
                    # DROP
                    dados = DATA_INIMIGOS.get(ent.nome)
                    if dados and "loot" in dados:
                        chance = dados.get("chance_loot", 0.0)
                        if random.random() < chance:
                            item_escolhido = random.choice(dados["loot"])
                            drop = LootDrop(ent.x, ent.y, item_escolhido)
                            self.items_no_chao.append(drop)
                            print(f"Loot Dropado: {item_escolhido}")

                    # XP e Remoção
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
            
        # Atualiza Textos
        for t in self.textos[:]:
            t.update()
            if t.life <= 0: self.textos.remove(t)

        # Atualiza Itens
        for loot in self.items_no_chao:
            loot.update(0.1)

    def criar_texto_dano(self, x, y, valor, cor=(255, 50, 50)):
        txt = efeitos.TextoFlutuante(x, y, str(valor), cor)
        self.textos.append(txt)