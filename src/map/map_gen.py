# src/map/map_gen.py
import logging
import math
import random
import pygame
from entities import actor
from graphics import efeitos
from graphics.particles import ParticleSystem
from .grid import Grid
from .spatial_hash import SpatialHash
from . import composicao
from .terrain import tile_is_blocking
# Novos imports necessários
from core import config
from core.context import GameContext
from .simulation import WorldSimulation
from .settings import WorldSettings
from .roads import RoadGenerator
from .terrain_generation import TerrainPainter, inside_ellipse
from .world_noise import WorldNoise

logger = logging.getLogger(__name__)

HARVESTABLE_CROPS = {
    "farm_carrot": ("Cenoura", 1),
    "farm_beet": ("Beterraba", 1),
    "farm_cabbage": ("Repolho", 1),
    "farm_onion": ("Cebola", 1),
    "farm_cauliflower": ("Couve-flor", 1),
    "nature_mushroom": ("Cogumelo", 2),
    "nature_mushroom_toxic": ("Cogumelo Estranho", 2),
}

CUSTOM_DECORATION_HITBOXES = {
    # Coordenadas relativas ao tile 32x32: (offset_x, offset_y, largura, altura)
    # Cerca horizontal: barra contínua de altura 14px na base dos mourões/trilhos
    "farm_fence_top": (0, 10, 32, 14),
    "farm_fence_bottom": (0, 10, 32, 14),
    "farm_fence_h": (0, 10, 32, 14),
    "farm_fence_h_left": (0, 10, 32, 14),
    "farm_fence_h_mid": (0, 10, 32, 14),
    "farm_fence_h_right": (0, 10, 32, 14),
    # Cerca vertical: mourão central de 12px de largura no centro do tile
    "farm_fence_left": (10, 0, 12, 32),
    "farm_fence_right": (10, 0, 12, 32),
    "farm_fence_v": (10, 0, 12, 32),
    # Cantos da cerca conectando os segmentos
    "farm_fence_corner_tl": (10, 10, 22, 22),
    "farm_fence_corner_tr": (0, 10, 22, 22),
    "farm_fence_corner_bl": (10, 0, 22, 22),
    "farm_fence_corner_br": (0, 0, 22, 22),
    # Props da cidade
    "town_well": (2, 8, 28, 22),
    "street_lamp": (11, 20, 10, 12),
    "barrel_wood": (4, 4, 24, 24),
    "crate_wood": (2, 2, 28, 28),
    "market_stall": (0, 10, 32, 22),
    "blacksmith_furnace": (2, 6, 28, 26),
    "blacksmith_anvil": (4, 10, 24, 20),
    "town_workbench": (2, 8, 28, 24),
    "town_bench": (2, 8, 28, 18),
    "town_bench_large": (0, 8, 32, 18),
}
FENCE_DECORATION_HITBOXES = CUSTOM_DECORATION_HITBOXES


class Mapa:
    def __init__(
        self,
        context: GameContext,
        seed: int | None = None,
        settings: WorldSettings | None = None,
    ):
        self.context = context
        self.content = context.content
        self.settings = settings or WorldSettings()
        self.largura = self.settings.width
        self.altura = self.settings.height
        self.grid_sistema = Grid(self.largura, self.altura)
        self.grid = self.grid_sistema.tiles
        self.spatial_index = SpatialHash(cell_tiles=4)
        
        self.entidades = []
        self.items_no_chao = [] # Lista para os drops
        self.safras_em_crescimento = [] # Vegetais e cogumelos colhidos aguardando regeneração
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        self.particulas = ParticleSystem()
        self.jogador = None
        self.camera = None
        self.desert_center = (0, 0)
        self.desert_radii = (1, 1)
        self.desert_tile_count = 0
        self.snow_center = (0, 0)
        self.snow_radii = (1, 1)
        self.snow_tile_count = 0
        self.ponds = []
        self.pond_tile_count = 0
        self.clareiras = []
        self.trilha_tiles = set()
        self.pontos_interesse = []
        self._tree_positions = set()
        self.bonfire_positions = set()
        self.town_lights = set()
        self.time_system = None
        self.seed = 0
        self.rng = random.Random()
        self.gameplay_rng = random.Random()
        self.simulation = WorldSimulation(self)
        self.gerar_novo_nivel(seed)

    def obter_tile(self, x, y):
        return self.grid_sistema.obter_tile(x, y)

    @staticmethod
    def dentro_do_deserto(x, y, center, radii, edge_noise=0.0):
        """Compatibilidade para consumidores da função geométrica antiga."""
        return inside_ellipse(x, y, center, radii, edge_noise)

    def desenhar_faixa_estrada(self, x1, y1, x2, y2, largura_estrada=3):
        """Compatibilidade para ferramentas antigas; delega ao gerador."""
        RoadGenerator(self, self.rng, self.settings)._draw_strip(
            x1, y1, x2, y2, largura_estrada
        )

    def gerar_estradas_walker(self):
        """Compatibilidade para ferramentas antigas; delega ao gerador."""
        RoadGenerator(self, self.rng, self.settings).generate()

    def is_blocked_terrain(self, x, y):
        tile = self.obter_tile(x, y)
        return tile_is_blocking(tile) if tile else True

    def get_tile_hitbox(self, x: int, y: int) -> pygame.Rect | None:
        """Retorna o retângulo de colisão preciso para o tile (x, y) ou None para o tile inteiro."""
        tile = self.obter_tile(x, y)
        if not tile:
            return None

        custom = getattr(tile, "custom_hitbox", None)
        if custom:
            ox, oy, w, h = custom
            tamanho = config.TAMANHO_TILE
            return pygame.Rect(int(x * tamanho + ox), int(y * tamanho + oy), int(w), int(h))

        decoracao = getattr(tile, "decoracao", None)
        if decoracao in FENCE_DECORATION_HITBOXES:
            ox, oy, w, h = FENCE_DECORATION_HITBOXES[decoracao]
            tamanho = config.TAMANHO_TILE
            return pygame.Rect(int(x * tamanho + ox), int(y * tamanho + oy), int(w), int(h))

        return None

    def _index_bonfires(self):
        self.bonfire_positions.clear()
        self.town_lights.clear()
        for y in range(self.altura):
            for x in range(self.largura):
                tile = self.obter_tile(x, y)
                if not tile:
                    continue
                if tile.decoracao == "nature_bonfire":
                    self.bonfire_positions.add((x, y))
                elif tile.decoracao in {"street_lamp", "blacksmith_furnace"}:
                    self.town_lights.add((x, y))

    def is_near_bonfire(self, x: float, y: float, radius: float = 4.5) -> bool:
        radius_sq = radius * radius
        all_lights = self.bonfire_positions | self.town_lights
        for bx, by in all_lights:
            cx = bx + 0.5
            cy = by + 0.5
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius_sq:
                return True
        return False

    def get_nearest_bonfire(self, x: float, y: float) -> tuple[float, float, float] | None:
        all_lights = self.bonfire_positions | self.town_lights
        if not all_lights:
            return None
        closest = None
        min_dist_sq = float("inf")
        for bx, by in all_lights:
            cx = bx + 0.5
            cy = by + 0.5
            d_sq = (x - cx) ** 2 + (y - cy) ** 2
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest = (cx, cy, math.sqrt(d_sq))
        return closest


    def alert_enemies(self, origin_x: float, origin_y: float, radius: float = 18.0) -> None:
        radius_sq = radius * radius
        for ent in self.entidades:
            if getattr(ent, "role", None) == "enemy" and getattr(ent, "ai", None):
                dx = ent.x - origin_x
                dy = ent.y - origin_y
                if dx * dx + dy * dy <= radius_sq:
                    ent.ai.on_hear_sound(origin_x, origin_y)

    def alert_allies(self, caller, radius: float = 7.0) -> None:
        radius_sq = radius * radius
        for ent in self.entidades:
            if ent is not caller and getattr(ent, "ai", None):
                same_group = (
                    (caller.role == "animal" and ent.role == "animal")
                    or (caller.role == "enemy" and ent.role == "enemy")
                )
                if same_group:
                    dx = ent.x - caller.x
                    dy = ent.y - caller.y
                    if dx * dx + dy * dy <= radius_sq:
                        ent.ai.on_ally_alert(caller)

    def gerar_novo_nivel(self, seed: int | None = None):
        self.entidades = []
        self.items_no_chao = []
        self.safras_em_crescimento = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        self.desert_tile_count = 0
        self.snow_tile_count = 0
        self.pond_tile_count = 0
        self.clareiras = []
        self.trilha_tiles = set()
        self.pontos_interesse = []
        self._tree_positions = set()
        self.bonfire_positions = set()
        
        self.seed = (
            random.SystemRandom().randint(0, 2**31 - 1)
            if seed is None
            else int(seed)
        )
        self.rng = random.Random(self.seed)
        self.gameplay_rng = random.Random(self.seed + 10_007)
        logger.info("Generating world with seed %s", self.seed)

        # 2. Preparar campos determinísticos de ruído.
        noise = WorldNoise(self.seed)
        margin = 28
        self.desert_center = (
            self.rng.randint(margin, self.largura - margin),
            self.rng.randint(margin, self.altura - margin),
        )
        self.desert_radii = (
            self.rng.randint(24, 34),
            self.rng.randint(20, 29),
        )
        self.snow_radii = (
            self.rng.randint(22, 30),
            self.rng.randint(19, 26),
        )
        self.snow_center = (self.largura - margin, margin)
        for _ in range(120):
            candidate = (
                self.rng.randint(margin, self.largura - margin),
                self.rng.randint(margin, self.altura - margin),
            )
            combined_radii = (
                self.desert_radii[0] + self.snow_radii[0] + 10,
                self.desert_radii[1] + self.snow_radii[1] + 10,
            )
            if composicao.distancia_eliptica(
                candidate[0], candidate[1], self.desert_center, combined_radii
            ) > 1.0:
                self.snow_center = candidate
                break

        pond_rng = random.Random(self.seed + 97)

        def centro_lagoa_valido(x, y, raio_x, raio_y):
            # As lagoas pequenas pertencem a áreas verdes. Evita o antigo aro
            # de grama surgindo no meio de praia, ruína ou mar aberto.
            amostras = (
                (x, y),
                (x - raio_x - 4, y),
                (x + raio_x + 4, y),
                (x, y - raio_y - 4),
                (x, y + raio_y + 4),
            )
            if any(
                noise.terrain(px, py) <= -0.02
                for px, py in amostras
            ):
                return False
            return noise.biome(x, y) < 0.08

        self.ponds = composicao.gerar_lagoas(
            self.largura,
            self.altura,
            pond_rng,
            regioes_excluidas=(
                (self.desert_center, self.desert_radii),
                (self.snow_center, self.snow_radii),
            ),
            quantidade=3,
            centro_valido=centro_lagoa_valido,
        )

        TerrainPainter(self, noise, self.rng).paint()

        # O atlas da lagoa possui bordas retas e cantos de 90 graus. Remove
        # pontas de um tile que exigiriam peças de três ou quatro lados e que,
        # sem essa limpeza, aparecem como quadrados azuis sem margem.
        self.pond_tile_count = composicao.suavizar_margens_lagoa(self)
        
        # --- 3.5 GERAR ESTRADAS (WALKER) ---
        RoadGenerator(self, self.rng, self.settings).generate()
        # -----------------------------------

        # 3.6 Compõe clareiras, trilhas e pequenas hortas conectadas.
        composicao.CompositorMundo(self, self.seed).gerar()
        self._index_bonfires()

        # Garante que estradas, vilas ou trilhas não deixem pontas de água
        # irregulares de 1 tile após a composição final do mundo.
        self.pond_tile_count = composicao.suavizar_margens_lagoa(self)

        # 4. Spawn do Jogador
        sx, sy = 15, 15
        encontrou = bool(self.clareiras)
        if encontrou:
            sx, sy = self.clareiras[0].centro
        else:
            for _ in range(100):
                tx = self.rng.randint(5, self.largura - 5)
                ty = self.rng.randint(5, self.altura - 5)
                if not self.is_blocked_terrain(tx, ty):
                    sx, sy = tx, ty
                    encontrou = True
                    break
        
        if not encontrou:
            tile = self.obter_tile(sx, sy)
            if tile: 
                tile.tipo = "terra"
                tile.bloqueado = False
                tile.decoracao = None
                tile.bioma = "clareira"

        if not self.jogador:
            self.jogador = actor.Entidade(
                sx, sy, "Survivor", self.context, rng=self.gameplay_rng
            )
        else:
            self.jogador.x, self.jogador.y = float(sx), float(sy)
            self.jogador.hp = self.jogador.hp_max
            self.jogador.physics.moving = False
            self.jogador.physics.update_hitbox()
        
        self.entidades.append(self.jogador)

        # 5. Spawn de Inimigos
        quantidade_monstros = self.settings.enemy_count
        count = 0
        tentativas = 0
        while count < quantidade_monstros and tentativas < 2000:
            tentativas += 1
            mx = self.rng.randint(5, self.largura - 5)
            my = self.rng.randint(5, self.altura - 5)
            
            dist = ((mx - sx)**2 + (my - sy)**2)**0.5
            if dist < 10: continue

            if not self.is_blocked_terrain(mx, my):
                v_ruido = noise.terrain(mx, my)
                v_bioma = noise.biome(mx, my)
                
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
                
                inimigo = actor.Entidade(
                    mx, my, nome, self.context, rng=self.gameplay_rng
                )
                self.entidades.append(inimigo)
                count += 1

        self._spawnar_npcs_vilas()
        self._spawnar_animais()
        self.spatial_index.rebuild(self.entidades)

    def _spawnar_npcs_vilas(self):
        """Spawna cidadãos, guardas, comerciantes e alquimistas nas vilas e cidades."""
        for clareira in self.clareiras[2:]:
            cx, cy = clareira.centro

            # 1. Guarda da Cidade na entrada
            pos_guarda = (cx, cy + 3)
            if 0 <= pos_guarda[0] < self.largura and 0 <= pos_guarda[1] < self.altura:
                if not self.is_blocked_terrain(*pos_guarda):
                    guarda = actor.Entidade(pos_guarda[0], pos_guarda[1], "Guarda da Cidade", self.context, rng=self.gameplay_rng)
                    self.entidades.append(guarda)

            # 2. Aldeão passeando pela praça
            pos_aldeao = (cx - 1, cy)
            if 0 <= pos_aldeao[0] < self.largura and 0 <= pos_aldeao[1] < self.altura:
                if not self.is_blocked_terrain(*pos_aldeao):
                    aldeao = actor.Entidade(pos_aldeao[0], pos_aldeao[1], "Aldeão", self.context, rng=self.gameplay_rng)
                    self.entidades.append(aldeao)

            # 3. Taberneira próxima às casas
            pos_taberneira = (cx - 3, cy - 2)
            if 0 <= pos_taberneira[0] < self.largura and 0 <= pos_taberneira[1] < self.altura:
                if not self.is_blocked_terrain(*pos_taberneira):
                    taberneira = actor.Entidade(pos_taberneira[0], pos_taberneira[1], "Taberneira", self.context, rng=self.gameplay_rng)
                    self.entidades.append(taberneira)

            # 4. Mercador na feira / barraca
            pos_mercador = (cx + 4, cy)
            if 0 <= pos_mercador[0] < self.largura and 0 <= pos_mercador[1] < self.altura:
                if not self.is_blocked_terrain(*pos_mercador):
                    mercador = actor.Entidade(pos_mercador[0], pos_mercador[1], "Mercador", self.context, rng=self.gameplay_rng)
                    self.entidades.append(mercador)

            # 5. Alquimista próximo aos canteiros
            pos_alquimista = (cx + 2, cy - 2)
            if 0 <= pos_alquimista[0] < self.largura and 0 <= pos_alquimista[1] < self.altura:
                if not self.is_blocked_terrain(*pos_alquimista):
                    alquimista = actor.Entidade(pos_alquimista[0], pos_alquimista[1], "Alquimista", self.context, rng=self.gameplay_rng)
                    self.entidades.append(alquimista)

    def _spawnar_animais(self):
        farm_species = [
            "Touro", "Bezerro", "Pintinho", "Cordeiro",
            "Porquinho", "Galo", "Ovelha", "Peru"
        ]
        hunt_species = [
            "Javali", "Cervo", "Raposa", "Lebre", "Galo Silvestre"
        ]

        # 1. Animais de Fazenda nas Vilas / Clareiras
        for clareira in self.clareiras:
            cx, cy = clareira.centro
            qtd_vila = self.rng.randint(3, 5)
            for _ in range(qtd_vila):
                for _tentativa in range(30):
                    ax = cx + self.rng.randint(-7, 7)
                    ay = cy + self.rng.randint(-7, 7)
                    if 0 <= ax < self.largura and 0 <= ay < self.altura:
                        if not self.is_blocked_terrain(ax, ay):
                            especie = self.rng.choice(farm_species)
                            animal = actor.Entidade(
                                ax, ay, especie, self.context, rng=self.gameplay_rng
                            )
                            self.entidades.append(animal)
                            break

        # 2. Animais Selvagens pela Natureza / Floresta / Margens
        total_selvagens = self.rng.randint(18, 28)
        spawned = 0
        tentativas = 0
        while spawned < total_selvagens and tentativas < 1500:
            tentativas += 1
            wx = self.rng.randint(6, self.largura - 6)
            wy = self.rng.randint(6, self.altura - 6)
            
            if self.jogador:
                dist = math.hypot(wx - self.jogador.x, wy - self.jogador.y)
                if dist < 8:
                    continue

            if not self.is_blocked_terrain(wx, wy):
                tile = self.obter_tile(wx, wy)
                if tile and tile.tipo in ("grass", "terra", "coast", "sand"):
                    especie = self.rng.choice(hunt_species)
                    animal = actor.Entidade(
                        wx, wy, especie, self.context, rng=self.gameplay_rng
                    )
                    self.entidades.append(animal)
                    spawned += 1

    def nearby_entities(self, rect):
        return self.spatial_index.query(rect)

    def update(self, dt):
        self.simulation.update(dt)
    def criar_texto_dano(self, x, y, valor, cor=(255, 50, 50)):
        txt = efeitos.TextoFlutuante(x, y, str(valor), cor)
        self.textos.append(txt)

    def colher_decoracao(self, x, y, atacante=None):
        """Colhe vegetal ou cogumelo no tile (x, y) e registra safra para rebrotar."""
        tile = self.obter_tile(x, y)
        if not tile or not tile.decoracao:
            return False

        decoracao = tile.decoracao
        if decoracao not in HARVESTABLE_CROPS:
            return False

        item_padrao, dias_brotar = HARVESTABLE_CROPS[decoracao]

        # Cogumelos silvestres têm chance de serem estranhos/alucinógenos
        if decoracao == "nature_mushroom":
            rng = getattr(self, "gameplay_rng", None) or getattr(self, "rng", None) or random
            item_name = "Cogumelo Estranho" if rng.random() < 0.30 else "Cogumelo"
        else:
            item_name = item_padrao

        current_day = self.time_system.day_count if hasattr(self, "time_system") and self.time_system else 1
        self.safras_em_crescimento.append({
            "x": x,
            "y": y,
            "especie": decoracao,
            "dia_colheita": current_day,
            "dias_para_brotar": dias_brotar,
        })

        tile.decoracao = None

        drop_x, drop_y = x + 0.5, y + 0.5
        if hasattr(self, "particulas") and self.particulas:
            self.particulas.emit(drop_x, drop_y, "leaf", 10)
            self.particulas.emit(drop_x, drop_y, "pickup", 6)

        from entities.loot import LootDrop
        loot = LootDrop(drop_x, drop_y, item_name, self.content)
        self.items_no_chao.append(loot)

        if hasattr(self, "criar_texto_dano"):
            self.criar_texto_dano(drop_x, drop_y - 0.5, f"Colheu {item_name}!", (120, 240, 140))

        logger.info("Harvested %s at (%d, %d) yielding %s", decoracao, x, y, item_name)
        return True

    def obter_decoracao_colhivel_proxima(self, px, py, raio=1.5):
        """Retorna (x, y, nome_item) da planta colhível mais próxima."""
        raio_tiles = int(math.ceil(raio))
        cx, cy = int(round(px)), int(round(py))
        melhor = None
        melhor_dist = float("inf")

        for dy in range(-raio_tiles, raio_tiles + 1):
            for dx in range(-raio_tiles, raio_tiles + 1):
                tx, ty = cx + dx, cy + dy
                dist = math.hypot(px - (tx + 0.5), py - (ty + 0.5))
                if dist > raio:
                    continue
                tile = self.obter_tile(tx, ty)
                if tile and tile.decoracao in HARVESTABLE_CROPS:
                    if dist < melhor_dist:
                        melhor_dist = dist
                        item_nome, _ = HARVESTABLE_CROPS[tile.decoracao]
                        melhor = (tx, ty, item_nome)
        return melhor

    def colher_mais_proximo(self, px, py, raio=1.5, jogador=None):
        proximo = self.obter_decoracao_colhivel_proxima(px, py, raio)
        if proximo:
            tx, ty, _ = proximo
            return self.colher_decoracao(tx, ty, jogador)
        return False

    def atualizar_regeneracao_safras(self, current_day=None):
        """Rebrota vegetais e cogumelos colhidos após o tempo necessário (1 ou 2 ciclos)."""
        if not hasattr(self, "safras_em_crescimento") or not self.safras_em_crescimento:
            return
        if current_day is None:
            current_day = self.time_system.day_count if hasattr(self, "time_system") and self.time_system else 1

        restantes = []
        for safra in self.safras_em_crescimento:
            x, y = safra["x"], safra["y"]
            especie = safra["especie"]
            dia_colheita = safra.get("dia_colheita", 1)
            dias_para_brotar = safra.get("dias_para_brotar", 1)

            if current_day - dia_colheita >= dias_para_brotar:
                tile = self.obter_tile(x, y)
                if tile and tile.decoracao is None:
                    tile.decoracao = especie
                    if hasattr(self, "particulas") and self.particulas:
                        self.particulas.emit(x + 0.5, y + 0.5, "leaf", 8)
                    logger.info("Crop %s regrew at (%d, %d) on day %d", especie, x, y, current_day)
            else:
                restantes.append(safra)
        self.safras_em_crescimento = restantes
