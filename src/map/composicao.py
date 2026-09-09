from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
import random


DECORACOES_BORDA = (
    "nature_sprout",
    "nature_leaf_cluster",
    "nature_mushroom",
    "nature_flower_white",
    "nature_flower_yellow",
    "nature_flower_purple",
    "nature_bush_green",
    "nature_fallen_leaves",
)

CULTIVOS_HORTA = (
    "farm_carrot",
    "farm_beet",
    "farm_cabbage",
    "farm_cauliflower",
    "farm_onion",
)


@dataclass(frozen=True)
class Lagoa:
    x: int
    y: int
    raio_x: int
    raio_y: int

    @property
    def centro(self):
        return self.x, self.y

    @property
    def raios(self):
        return self.raio_x, self.raio_y


@dataclass(frozen=True)
class Clareira:
    x: int
    y: int
    raio_x: int
    raio_y: int

    @property
    def centro(self):
        return self.x, self.y


@dataclass(frozen=True)
class PontoInteresse:
    tipo: str
    x: int
    y: int

    @property
    def centro(self):
        return self.x, self.y


def distancia_eliptica(x, y, centro, raios):
    raio_x, raio_y = raios
    return (
        ((x - centro[0]) / raio_x) ** 2
        + ((y - centro[1]) / raio_y) ** 2
    )


def classificar_lagoa(x, y, lagoas, ruido_borda=0.0):
    """Retorna o núcleo ou a margem de uma lagoa irregular."""
    if not lagoas:
        return None
    distancia = min(
        distancia_eliptica(x, y, lagoa.centro, lagoa.raios)
        for lagoa in lagoas
    )
    distancia += ruido_borda * 0.24
    if distancia <= 1.0:
        return "agua"
    if distancia <= 1.48:
        return "margem"
    return None


def suavizar_margens_lagoa(mapa, passagens=2):
    """Remove pontas de água que o conjunto de oito bordas não representa.

    As peças do atlas cobrem lados retos e cantos adjacentes. Um tile de água
    cercado por terra em três lados, ou em dois lados opostos, não possui uma
    peça correspondente e aparece como um quadrado sem contorno. A limpeza é
    simultânea por passagem para não depender da ordem de leitura do grid.
    """
    cardinais = {
        "north": (0, -1),
        "south": (0, 1),
        "west": (-1, 0),
        "east": (1, 0),
    }
    opostos = ({"north", "south"}, {"west", "east"})

    for _ in range(max(0, passagens)):
        remover = []
        for y in range(mapa.altura):
            for x in range(mapa.largura):
                tile = mapa.obter_tile(x, y)
                if not tile or tile.tipo != "deep_water" or tile.bioma != "lagoa":
                    continue

                terra = set()
                for lado, (dx, dy) in cardinais.items():
                    vizinho = mapa.obter_tile(x + dx, y + dy)
                    if vizinho and vizinho.tipo not in {"deep_water", "bridge"}:
                        terra.add(lado)

                if len(terra) >= 3 or any(par <= terra for par in opostos):
                    remover.append(tile)

        if not remover:
            break
        for tile in remover:
            tile.tipo = "grass"
            tile.bloqueado = False
            tile.decoracao = None
            tile.bioma = "lagoa"

    return sum(
        1
        for row in mapa.grid
        for tile in row
        if tile.tipo == "deep_water" and tile.bioma == "lagoa"
    )


def gerar_lagoas(
    largura,
    altura,
    rng: random.Random,
    regioes_excluidas=(),
    quantidade=3,
    centro_valido=None,
):
    """Cria definições espaçadas; a pintura ocorre junto do terreno-base."""
    lagoas = []
    tentativas = 0
    limite_tentativas = max(400, quantidade * 250)
    while len(lagoas) < quantidade and tentativas < limite_tentativas:
        tentativas += 1
        raio_x = rng.randint(5, 9)
        raio_y = rng.randint(4, 7)
        x = rng.randint(raio_x + 8, largura - raio_x - 9)
        y = rng.randint(raio_y + 8, altura - raio_y - 9)

        if centro_valido and not centro_valido(x, y, raio_x, raio_y):
            continue

        conflita = False
        for centro, raios in regioes_excluidas:
            soma_x = raio_x + raios[0] + 7
            soma_y = raio_y + raios[1] + 7
            if distancia_eliptica(x, y, centro, (soma_x, soma_y)) <= 1.0:
                conflita = True
                break
        if conflita:
            continue

        for existente in lagoas:
            soma_x = raio_x + existente.raio_x + 6
            soma_y = raio_y + existente.raio_y + 6
            if distancia_eliptica(x, y, existente.centro, (soma_x, soma_y)) <= 1.0:
                conflita = True
                break
        if not conflita:
            lagoas.append(Lagoa(x, y, raio_x, raio_y))
    return lagoas


class CompositorMundo:
    """Transforma o terreno aleatório em clareiras, trilhas e pequenos cenários."""

    def __init__(self, mapa_obj, seed):
        self.mapa = mapa_obj
        self.rng = random.Random(seed + 711)
        self.seed = seed
        self.clareiras = []
        self.trilha_tiles = set()
        self.pontos_interesse = []

    def gerar(self, quantidade_clareiras=6):
        self.clareiras = self._selecionar_clareiras(quantidade_clareiras)
        for clareira in self.clareiras:
            self._pintar_clareira(clareira)
        self._conectar_clareiras()
        self._plantar_hortas()
        self._montar_acampamentos()
        # Vilas nas clareiras restantes (índices 2 em diante)
        for clareira in self.clareiras[2:]:
            self._montar_vila(clareira)
        self.mapa.clareiras = list(self.clareiras)
        self.mapa.trilha_tiles = set(self.trilha_tiles)
        self.mapa.pontos_interesse = list(self.pontos_interesse)
        return self.clareiras

    def _selecionar_clareiras(self, quantidade):
        candidatos = []
        for _ in range(1200):
            raio_x = self.rng.randint(6, 9)
            raio_y = self.rng.randint(5, 7)
            margem_x = max(raio_x + 4, min(24, self.mapa.largura // 5))
            margem_y = max(raio_y + 4, min(16, self.mapa.altura // 5))
            max_x = self.mapa.largura - margem_x - 1
            max_y = self.mapa.altura - margem_y - 1
            if margem_x > max_x or margem_y > max_y:
                break
            candidato = Clareira(
                self.rng.randint(margem_x, max_x),
                self.rng.randint(margem_y, max_y),
                raio_x,
                raio_y,
            )
            proporcao, agua = self._proporcao_florestal(candidato)
            if agua == 0 and proporcao >= 0.76:
                candidatos.append((proporcao, candidato))

        # Escolher os candidatos mais puros primeiro também faz o spawn e os
        # pontos de interesse nascerem em enquadramentos visualmente coerentes.
        candidatos.sort(key=lambda item: item[0], reverse=True)
        escolhidas = []
        for _, candidato in candidatos:
            x, y = candidato.centro
            if any(
                math.hypot(x - outra.x, y - outra.y)
                < max(16, candidato.raio_x + outra.raio_x + 4)
                for outra in escolhidas
            ):
                continue
            escolhidas.append(candidato)
            if len(escolhidas) >= quantidade:
                break
        return escolhidas

    def _proporcao_florestal(self, clareira):
        amostras = 0
        floresta = 0
        agua = 0
        for y in range(clareira.y - clareira.raio_y, clareira.y + clareira.raio_y + 1, 2):
            for x in range(clareira.x - clareira.raio_x, clareira.x + clareira.raio_x + 1, 2):
                if distancia_eliptica(x, y, clareira.centro, (clareira.raio_x, clareira.raio_y)) > 1:
                    continue
                tile = self.mapa.obter_tile(x, y)
                if not tile:
                    continue
                amostras += 1
                if tile.tipo == "deep_water":
                    agua += 1
                if getattr(tile, "bioma", None) == "floresta":
                    floresta += 1
        proporcao = floresta / amostras if amostras else 0.0
        return proporcao, agua

    def _pintar_clareira(self, clareira):
        livres = set()
        for y in range(clareira.y - clareira.raio_y, clareira.y + clareira.raio_y + 1):
            for x in range(clareira.x - clareira.raio_x, clareira.x + clareira.raio_x + 1):
                distancia = distancia_eliptica(
                    x, y, clareira.centro, (clareira.raio_x, clareira.raio_y)
                )
                if distancia > 1.0:
                    continue
                tile = self.mapa.obter_tile(x, y)
                if not tile or tile.tipo == "deep_water":
                    continue
                tile.tipo = "terra" if distancia < 0.58 else "grass"
                tile.bloqueado = False
                tile.decoracao = None
                tile.bioma = "clareira"
                livres.add((x, y))
                if 0.63 <= distancia <= 1.0 and self.rng.random() < 0.28:
                    tile.decoracao = self.rng.choice(DECORACOES_BORDA)
        self._remover_arvores(livres)

    def _conectar_clareiras(self):
        if len(self.clareiras) < 2:
            return
        conectadas = [self.clareiras[0]]
        restantes = list(self.clareiras[1:])
        while restantes:
            origem, destino = min(
                (
                    (origem, destino)
                    for origem in conectadas
                    for destino in restantes
                ),
                key=lambda par: math.dist(par[0].centro, par[1].centro),
            )
            caminho = self._encontrar_caminho(origem.centro, destino.centro)
            self._pintar_trilha(caminho)
            conectadas.append(destino)
            restantes.remove(destino)

    def _encontrar_caminho(self, inicio, destino):
        fronteira = [(0.0, inicio)]
        veio_de = {inicio: None}
        custos = {inicio: 0.0}
        while fronteira:
            _, atual = heapq.heappop(fronteira)
            if atual == destino:
                break
            x, y = atual
            for vizinho in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                nx, ny = vizinho
                tile = self.mapa.obter_tile(nx, ny)
                if not tile or tile.tipo == "deep_water":
                    continue
                custo_passo = 1.0
                if tile.tipo in {"parede", "rocha"} or tile.bloqueado:
                    custo_passo = 6.0
                elif tile.tipo in {"sand", "mud"}:
                    custo_passo = 2.2
                elif tile.tipo == "estrada":
                    custo_passo = 0.75
                ondulacao = ((nx * 37 + ny * 19 + self.seed) % 9) * 0.025
                novo_custo = custos[atual] + custo_passo + ondulacao
                if vizinho not in custos or novo_custo < custos[vizinho]:
                    custos[vizinho] = novo_custo
                    prioridade = novo_custo + math.dist(vizinho, destino)
                    heapq.heappush(fronteira, (prioridade, vizinho))
                    veio_de[vizinho] = atual

        if destino not in veio_de:
            return []
        caminho = []
        atual = destino
        while atual is not None:
            caminho.append(atual)
            atual = veio_de[atual]
        caminho.reverse()
        return caminho

    def _pintar_trilha(self, caminho):
        livres = set()
        for centro_x, centro_y in caminho:
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                x, y = centro_x + dx, centro_y + dy
                tile = self.mapa.obter_tile(x, y)
                if not tile or tile.tipo == "deep_water":
                    continue
                if tile.tipo != "estrada":
                    tile.tipo = "terra"
                    tile.bioma = "trilha"
                tile.bloqueado = False
                tile.decoracao = None
                livres.add((x, y))
                self.trilha_tiles.add((x, y))
        self._remover_arvores(livres)

    def _plantar_hortas(self):
        for clareira in self.clareiras[:1]:
            ocupados = set()
            for y in range(clareira.y - 2, clareira.y + 3):
                for x in range(clareira.x - 3, clareira.x + 4):
                    tile = self.mapa.obter_tile(x, y)
                    if not tile or tile.tipo == "deep_water":
                        continue
                    tile.tipo = "terra"
                    tile.bioma = "horta"
                    tile.bloqueado = False
                    tile.decoracao = None
                    ocupados.add((x, y))
                    corredor = x == clareira.x
                    if not corredor and (x + y) % 2 == 0:
                        indice = (x * 5 + y * 3 + self.seed) % len(CULTIVOS_HORTA)
                        tile.decoracao = CULTIVOS_HORTA[indice]
            self._remover_arvores(ocupados)
            self._cercar_horta(clareira)
            self.pontos_interesse.append(
                PontoInteresse("horta_abandonada", clareira.x, clareira.y)
            )

    def _cercar_horta(self, clareira):
        """Monta uma cerca visual modular, deixando entradas no eixo central."""
        pecas = (
            (clareira.x - 2, clareira.y - 3, "farm_fence_top"),
            (clareira.x + 2, clareira.y - 3, "farm_fence_top"),
            (clareira.x - 2, clareira.y + 3, "farm_fence_bottom"),
            (clareira.x + 2, clareira.y + 3, "farm_fence_bottom"),
            (clareira.x - 4, clareira.y - 1, "farm_fence_left"),
            (clareira.x - 4, clareira.y + 1, "farm_fence_left"),
            (clareira.x + 4, clareira.y - 1, "farm_fence_right"),
            (clareira.x + 4, clareira.y + 1, "farm_fence_right"),
        )
        for x, y, decoracao in pecas:
            tile = self.mapa.obter_tile(x, y)
            if not tile:
                continue
            tile.tipo = "terra"
            tile.bioma = "horta"
            tile.bloqueado = False
            tile.decoracao = decoracao

        # A colisão acompanha somente a base visível da cerca. As aberturas
        # centrais de cima e de baixo continuam livres como pequenos portões.
        for y in (clareira.y - 3, clareira.y + 3):
            for dx in (-3, -2, -1, 1, 2, 3):
                tile = self.mapa.obter_tile(clareira.x + dx, y)
                if tile:
                    tile.bloqueado = True
        for x in (clareira.x - 4, clareira.x + 4):
            for dy in range(-2, 3):
                tile = self.mapa.obter_tile(x, clareira.y + dy)
                if tile:
                    tile.bloqueado = True

        # A trilha que chega à horta define automaticamente a posição do
        # portão, inclusive quando se aproxima por uma lateral.
        for x, y in self.trilha_tiles:
            if (
                clareira.x - 4 <= x <= clareira.x + 4
                and clareira.y - 3 <= y <= clareira.y + 3
            ):
                tile = self.mapa.obter_tile(x, y)
                if tile:
                    tile.bloqueado = False

    def _montar_acampamentos(self):
        for clareira in self.clareiras[1:2]:
            ocupados = set()
            for y in range(clareira.y - 3, clareira.y + 4):
                for x in range(clareira.x - 4, clareira.x + 5):
                    distancia = distancia_eliptica(
                        x,
                        y,
                        clareira.centro,
                        (4.5, 3.5),
                    )
                    if distancia > 1.0:
                        continue
                    tile = self.mapa.obter_tile(x, y)
                    if not tile or tile.tipo == "deep_water":
                        continue
                    tile.tipo = "terra"
                    tile.bioma = "acampamento"
                    tile.bloqueado = False
                    tile.decoracao = None
                    ocupados.add((x, y))

            bonfire_dx, bonfire_dy = next(
                (
                    (dx, dy)
                    for dx, dy in ((2, -1), (-2, -1), (0, -2), (2, 1))
                    if (clareira.x + dx, clareira.y + dy) not in self.trilha_tiles
                ),
                (2, -1),
            )
            decoracoes = (
                (bonfire_dx, bonfire_dy, "nature_bonfire"),
                (-2, 0, "nature_stump"),
                (2, 0, "nature_stump"),
                (0, 2, "nature_stump"),
                (-2, -2, "nature_twig"),
                (2, -2, "nature_pebble_gray"),
            )
            for dx, dy, decoracao in decoracoes:
                tile = self.mapa.obter_tile(clareira.x + dx, clareira.y + dy)
                if tile:
                    tile.decoracao = decoracao

            bonfire_tile = self.mapa.obter_tile(
                clareira.x + bonfire_dx,
                clareira.y + bonfire_dy,
            )
            if bonfire_tile:
                bonfire_tile.bloqueado = True

            self._remover_arvores(ocupados)
            self.pontos_interesse.append(
                PontoInteresse("acampamento", clareira.x, clareira.y)
            )

    def _remover_arvores(self, coordenadas):
        if not coordenadas:
            return
        removidas = {
            entidade
            for entidade in self.mapa.entidades
            if "tree" in entidade.tags
            and (int(entidade.x), int(entidade.y)) in coordenadas
        }
        if removidas:
            self.mapa.entidades = [
                entidade
                for entidade in self.mapa.entidades
                if entidade not in removidas
            ]
        posicoes = getattr(self.mapa, "_tree_positions", None)
        if posicoes is not None:
            posicoes.difference_update(coordenadas)

    # ------------------------------------------------------------------
    # VILAS: três casas de layout fixo ao redor da clareira
    # ------------------------------------------------------------------

    # Layout relativo de cada casa: (offset_cx, offset_cy, tipo_telhado)
    # Tipo de telhado controla a decoração central (porta/janela voltadas ao sul)
    _LAYOUTS_CASA = [
        # Casa 1 – ao norte-oeste da clareira
        {"dx": -8, "dy": -8, "w": 5, "h": 4,
         "porta_lado": "sul", "decoracao_porta": "house_door_front",
         "decoracao_janela": "house_window_front"},
        # Casa 2 – ao norte-leste da clareira
        {"dx": 4,  "dy": -8, "w": 5, "h": 4,
         "porta_lado": "sul", "decoracao_porta": "house_door_wood",
         "decoracao_janela": "house_window_shutters"},
        # Casa 3 – ao sul (centro) da clareira
        {"dx": -2, "dy": 5,  "w": 5, "h": 4,
         "porta_lado": "norte", "decoracao_porta": "house_door_front",
         "decoracao_janela": "house_window_front"},
    ]

    def _montar_vila(self, clareira):
        """Constrói três casas em posições fixas ao redor da clareira."""
        cx, cy = clareira.centro
        ocupados = set()
        for layout in self._LAYOUTS_CASA:
            casa_x = cx + layout["dx"]
            casa_y = cy + layout["dy"]
            ocupados |= self._construir_casa(
                casa_x, casa_y,
                layout["w"], layout["h"],
                porta_lado=layout["porta_lado"],
                decoracao_porta=layout["decoracao_porta"],
                decoracao_janela=layout["decoracao_janela"],
            )
        self._remover_arvores(ocupados)
        self.pontos_interesse.append(
            PontoInteresse("vila", cx, cy)
        )

    def _construir_casa(self, ox, oy, largura, altura,
                         porta_lado="sul",
                         decoracao_porta="house_door_front",
                         decoracao_janela="house_window_front"):
        """Pinta o chão e coloca as decorações de uma casa de tamanho fixo.

        Convenção de coordenadas:
        - (ox, oy) é o canto superior-esquerdo da casa
        - largura e altura estão em tiles
        - As paredes são a borda exterior; o interior é chão de terra
        - A porta está sempre centrada no lado indicado (livre ao passar)
        - Uma janela fica a 1 tile da porta na mesma parede
        """
        ocupados = set()

        # 1. Pintar INTERIOR como chão de terra transitável
        for dy in range(1, altura - 1):
            for dx in range(1, largura - 1):
                tile = self.mapa.obter_tile(ox + dx, oy + dy)
                if tile and tile.tipo != "deep_water":
                    self._pintar_chao_casa(tile)
                    ocupados.add((ox + dx, oy + dy))

        # 2. Pintar PAREDES bloqueadas (borda)
        for dx in range(largura):
            for dy in range(altura):
                if 0 < dx < largura - 1 and 0 < dy < altura - 1:
                    continue  # interior já pintado
                tile = self.mapa.obter_tile(ox + dx, oy + dy)
                if tile and tile.tipo != "deep_water":
                    tile.tipo = "parede"
                    tile.bloqueado = True
                    tile.decoracao = None
                    tile.bioma = "vila"
                    ocupados.add((ox + dx, oy + dy))

        # 3. Posicionar PORTA (centro da parede exterior, livre)
        cx_casa = ox + largura // 2
        cy_casa = oy + altura // 2
        if porta_lado == "sul":
            px, py = cx_casa, oy + altura - 1
        elif porta_lado == "norte":
            px, py = cx_casa, oy
        elif porta_lado == "leste":
            px, py = ox + largura - 1, cy_casa
        else:  # oeste
            px, py = ox, cy_casa

        porta_tile = self.mapa.obter_tile(px, py)
        if porta_tile:
            porta_tile.tipo = "terra"
            porta_tile.bloqueado = False
            porta_tile.decoracao = decoracao_porta
            porta_tile.bioma = "vila"
            ocupados.add((px, py))

        # 4. Posicionar JANELA (1 tile à direita da porta na mesma parede)
        if porta_lado in ("sul", "norte"):
            jx, jy = px + 1, py
        else:
            jx, jy = px, py + 1
        janela_tile = self.mapa.obter_tile(jx, jy)
        if janela_tile and (jx, jy) != (px, py):
            janela_tile.tipo = "parede"
            janela_tile.bloqueado = True
            janela_tile.decoracao = decoracao_janela
            janela_tile.bioma = "vila"
            ocupados.add((jx, jy))

        # 5. Chaminé no canto oposto à porta
        if porta_lado == "sul":
            chx, chy = ox + largura - 2, oy
        elif porta_lado == "norte":
            chx, chy = ox + largura - 2, oy + altura - 1
        elif porta_lado == "leste":
            chx, chy = ox, oy
        else:
            chx, chy = ox + largura - 1, oy
        chamine_tile = self.mapa.obter_tile(chx, chy)
        if chamine_tile:
            chamine_tile.decoracao = "house_chimney"

        return ocupados

    @staticmethod
    def _pintar_chao_casa(tile):
        """Torna o tile um chão de terra de interior de casa."""
        tile.tipo = "terra"
        tile.bloqueado = False
        tile.decoracao = None
        tile.bioma = "vila"
