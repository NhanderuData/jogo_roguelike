# src/map_gen.py
import random
from graphics import config
from entities import actor
from graphics import efeitos

class Mapa:
    def __init__(self):
        self.grid = []
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        self.jogador = None
        self.nivel = 1
        self.gerar_novo_nivel()

    def is_blocked_terrain(self, x, y):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= config.LARGURA_MAPA or iy < 0 or iy >= config.ALTURA_MAPA: 
            return True
        # Se for Parede (1), Rocha (5), etc. (Ajuste os IDs conforme seu config)
        if self.grid[iy][ix] in [1, 5]: 
            return True
        return False

    def gerar_novo_nivel(self):
        self.grid = [[0 for _ in range(config.LARGURA_MAPA)] for _ in range(config.ALTURA_MAPA)]
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        
        sx, sy = config.TAMANHO_CHUNK // 2, config.TAMANHO_CHUNK // 2
        
        # --- CORREÇÃO: Herói agora recebe xp_reward=0 ---
        if not self.jogador: 
            self.jogador = actor.Entidade(sx, sy, "Heroi", 100, 10, xp_reward=0)
        else: 
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
        
        self.entidades.append(self.jogador)
        
        for y in range(config.CHUNKS_Y):
            for x in range(config.CHUNKS_X):
                self.gerar_chunk(x * config.TAMANHO_CHUNK, y * config.TAMANHO_CHUNK, random.choice(["floresta", "ruinas"]))

    def gerar_chunk(self, ox, oy, tipo):
        for y in range(config.TAMANHO_CHUNK):
            for x in range(config.TAMANHO_CHUNK):
                if x < 2 or y < 2 or x > 28 or y > 28: continue
                gx, gy = ox + x, oy + y
                rng = random.randint(0, 100)
                
                if tipo == "floresta":
                    # --- CORREÇÃO: Em vez de ID no grid, criamos a Árvore como Entidade ---
                    if rng < 10: 
                        # Cria árvore com 50 HP e 5 XP de recompensa
                        arv = actor.ObjetoDestrutivel(gx, gy, "Arvore", hp=50)
                        self.entidades.append(arv)
                    elif rng < 12: 
                        self.grid[gy][gx] = 5 # Rocha (ainda estática)
                elif tipo == "ruinas":
                    if rng < 5: self.grid[gy][gx] = 1 # Parede
                    elif rng < 8: self.grid[gy][gx] = 5
                    elif rng < 12: self.grid[gy][gx] = 6 # Tapete

        # SPAWN DE INIMIGOS
        qtd = random.randint(2, 4)
        for _ in range(qtd):
            mx = ox + random.randint(5, 25)
            my = oy + random.randint(5, 25)
            if not self.is_blocked_terrain(mx, my):
                nome = "Orc" if tipo == "floresta" else "Troll"
                hp = 30 if nome == "Orc" else 80
                dano = 5 if nome == "Orc" else 15
                xp = 15 if nome == "Orc" else 50 # Recompensa de XP
                self.entidades.append(actor.Entidade(mx, my, nome, hp, dano, xp_reward=xp))

    def update(self):
        # Remove entidades mortas (HP <= 0)
        for ent in self.entidades[:]:
            ent.update()
            ent.update_ia(self)
            
            if ent.hp <= 0:
                if ent != self.jogador:
                    self.jogador.ganhar_xp(ent.xp_reward) # Dá XP pro herói
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
        cor = getattr(config, 'COR_DANO_JOGADOR', (255, 50, 50)) 
        txt = efeitos.TextoFlutuante(x, y, str(valor), cor)
        self.textos.append(txt)