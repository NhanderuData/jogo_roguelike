# src/entidades.py
import math
import random
import pygame
from graphics import config
from graphics import recursos
from entities import combat

class Entidade:
    def __init__(self, x, y, nome, hp, dano, xp_reward=0):
        # 1. Atributos Básicos
        self.x = float(x)
        self.y = float(y)
        self.nome = nome
        self.hp_max = hp
        self.hp = hp
        self.dano = dano
        self.off_z = 0  # Altura (pulo/degrau)

        # 2. Configurações de Nível e RPG
        self.xp = 0
        self.nivel = 1
        self.xp_proximo_nivel = 20
        self.xp_reward = xp_reward
        self.speed = 0.15 if nome == "Heroi" else 0.04

        # 3. Cooldowns de Combate
        self.cooldown_tiro = 0
        self.cooldown_espada = 0

        # 4. CONFIGURAÇÃO VISUAL (Definida ANTES da hitbox para evitar erros)
        configs_visuais = {
            "Heroi":      { "sombra": 1.2, "ajuste_x": 0, "ajuste_y": 0 }, 
            "Orc":        { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Troll":      { "sombra": 2.0, "ajuste_x": 0, "ajuste_y": 0 },
            "REI TROLL":  { "sombra": 3.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Arvore":     { "sombra": 1.5, "ajuste_x": 0, "ajuste_y": 0 },
            "RedTree":    { "sombra": 1.5, "ajuste_x": 0, "ajuste_y": 0 },
        }

        dados = configs_visuais.get(nome, { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 })
        self.scale_sombra = dados["sombra"]
        self.offset_x = dados["ajuste_x"]
        self.offset_y = dados["ajuste_y"]

        # 5. Definição da Hitbox
        # Hitbox mais curta (0.4) foca nos pés e evita travar em paredes "atrás" da cabeça
        self.largura_hb = 0.6 
        self.altura_hb = 0.4 
        self.hitbox = pygame.Rect(0, 0, 0, 0)

        # 6. Carregamento de Sprites
        key = "orc_run"
        if nome == "Heroi": key = "llama_run"
        elif nome == "Troll": key = "troll_run"
        elif nome == "REI TROLL": key = "boss_run"
        elif nome == "Arvore": key = "tree"
        elif nome == "RedTree": key = "red_tree"

        self.frames = recursos.SPRITES.get(key)
        self.frame_index = 0.0
        self.image = self.frames[0] if self.frames else None
        self.moving = False

        # 7. INICIALIZAÇÃO DA HITBOX
        # Chamada SOMENTE agora, que offsets e atributos já existem
        self.atualizar_hitbox()

    def atualizar_hitbox(self):
        """ Sincroniza o retângulo de colisão com a posição visual """
        tamanho = config.TAMANHO_TILE

        # Define o tamanho do retângulo
        largura = int(tamanho * self.largura_hb)
        altura = int(tamanho * self.altura_hb)

        if self.hitbox.width != largura or self.hitbox.height != altura:
            self.hitbox.size = (largura, altura)
        
        # Converte coordenadas de TILE (0, 1, 2...) para PIXELS (0, 32, 64...)
        px_x = self.x * tamanho
        px_y = self.y * tamanho

        # --- CORREÇÃO DO POSICIONAMENTO ---
        # CenterX: Pega o pixel X + metade do tile + ajuste visual
        self.hitbox.centerx = int(px_x + (tamanho // 2) + self.offset_x)
        
        # Bottom: Pega o pixel Y + tile inteiro (o chão) + ajuste visual - altura Z
        # Isso garante que a hitbox fique nos PÉS da entidade
        self.hitbox.bottom = int(px_y + tamanho + self.offset_y - self.off_z)

    def tomar_dano(self, qtd, mapa_obj=None):
        self.hp -= qtd
        if mapa_obj:
            mapa_obj.criar_texto_dano(self.x, self.y, int(qtd))

    def ganhar_xp(self, qtd):
        self.xp += qtd
        if self.xp >= self.xp_proximo_nivel:
            self.xp -= self.xp_proximo_nivel
            self.nivel += 1
            self.hp_max += 10
            self.hp = self.hp_max
            self.xp_proximo_nivel = int(self.xp_proximo_nivel * 1.5)

    def animar(self):
        # Otimização: Se a velocidade é 0 (Árvore), não processa animação
        if self.speed == 0:
            return 

        if self.moving and self.frames:
            self.frame_index += config.VELOCIDADE_ANIMACAO
            if self.frame_index >= len(self.frames): 
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
            
        elif self.frames:
            # Reseta para frame 0 se parar de andar
            self.frame_index = 0
            self.image = self.frames[0]
            
        self.moving = False

    def atirar(self, tx, ty, mapa_obj, origem):
        if self.cooldown_tiro > 0: return
        combat.criar_projetil(self.x, self.y, tx, ty, origem, mapa_obj)
        self.cooldown_tiro = 40 

    def atacar_espada(self, tx, ty, mapa_obj):
        if self.cooldown_espada > 0: return
        combat.executar_golpe_espada(self, tx, ty, mapa_obj)
        self.cooldown_espada = 30 

    def update(self, mapa_obj):
        if self.cooldown_tiro > 0: self.cooldown_tiro -= 1
        if self.cooldown_espada > 0: self.cooldown_espada -= 1
        
        # --- CORREÇÃO DE ALTURA (Z-LEVEL) ---
        # Verifica em qual tile a entidade está pisando
        tile_atual = mapa_obj.obter_tile(self.x, self.y)
        if tile_atual:
            # Pega o offset visual do tile (ex: 16px se for nível 1)
            # Se a entidade sobe num bloco de terra, a hitbox sobe junto
            self.off_z = tile_atual.get_offset_y()
        else:
            self.off_z = 0

        # Atualiza a hitbox AGORA, considerando a nova posição e nova altura
        self.atualizar_hitbox()
        self.animar()

    def update_ia(self, mapa_obj):
        if self.nome == "Heroi" or self.speed == 0: return 

        player = mapa_obj.jogador
        dist = ((self.x - player.x)**2 + (self.y - player.y)**2)**0.5
        
        if 0.8 < dist < 10: 
            dx = (player.x - self.x) / dist
            dy = (player.y - self.y) / dist
            
            nx = self.x + dx * self.speed
            ny = self.y + dy * self.speed
            
            if not mapa_obj.is_blocked_terrain(nx, self.y): self.x = nx
            if not mapa_obj.is_blocked_terrain(self.x, ny): self.y = ny
            self.moving = True

        if dist < 8:
            if dist < 1.5:
                self.atacar_espada(player.x, player.y, mapa_obj)
            elif dist > 3 and ("Troll" in self.nome or "REI" in self.nome):
                if random.randint(0, 100) < 5:
                    self.atirar(player.x, player.y, mapa_obj, "enemy")

# --- CLASSE PARA OBJETOS DESTRUTÍVEIS (ÁRVORES) ---
class ObjetoDestrutivel(Entidade):
    def __init__(self, x, y, nome, hp):
        super().__init__(x, y, nome, hp, dano=0, xp_reward=5)
        self.speed = 0 # Árvores não andam
        self.sombra_cache = None
        
    def update_ia(self, mapa_obj):
        pass # Árvores não pensam