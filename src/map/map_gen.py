# src/map/map_gen.py
import logging
import math
import random
from entities import actor
from graphics import efeitos
from graphics.particles import ParticleSystem
from .grid import Grid
from .spatial_hash import SpatialHash
from . import composicao
from .terrain import tile_is_blocking
# Novos imports necessários
from core.context import GameContext
from .simulation import WorldSimulation
from .settings import WorldSettings
from .roads import RoadGenerator
from .terrain_generation import TerrainPainter, inside_ellipse
from .world_noise import WorldNoise

logger = logging.getLogger(__name__)

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

    def _index_bonfires(self):
        self.bonfire_positions.clear()
        for y in range(self.altura):
            for x in range(self.largura):
                tile = self.obter_tile(x, y)
                if tile and tile.decoracao == "nature_bonfire":
                    self.bonfire_positions.add((x, y))

    def is_near_bonfire(self, x: float, y: float, radius: float = 4.5) -> bool:
        radius_sq = radius * radius
        for bx, by in self.bonfire_positions:
            cx = bx + 0.5
            cy = by + 0.5
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius_sq:
                return True
        return False

    def get_nearest_bonfire(self, x: float, y: float) -> tuple[float, float, float] | None:
        if not self.bonfire_positions:
            return None
        closest = None
        min_dist_sq = float("inf")
        for bx, by in self.bonfire_positions:
            cx = bx + 0.5
            cy = by + 0.5
            d_sq = (x - cx) ** 2 + (y - cy) ** 2
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
                closest = (cx, cy, math.sqrt(d_sq))
        return closest

    def gerar_novo_nivel(self, seed: int | None = None):
        # 1. Reset das Listas
        self.entidades = []
        self.items_no_chao = []
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

        self._spawnar_animais()
        self.spatial_index.rebuild(self.entidades)

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
