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
    # VILAS: três casas completas organizadas ao redor de uma praça
    # ------------------------------------------------------------------

    # dx/dy apontam para a âncora central da fachada. O footprint físico se
    # estende para cima; o sprite inclui o telhado e o beiral sem transformar
    # cada tile da construção em um pedaço desconexo de parede.
    _LAYOUTS_CASA = (
        {
            "dx": -4,
            "dy": -3,
            "largura": 5,
            "profundidade": 3,
            "sprite": "village_house_amber",
            "rota_horizontal": False,
        },
        {
            "dx": 4,
            "dy": -3,
            "largura": 5,
            "profundidade": 3,
            "sprite": "village_house_brick",
            "rota_horizontal": False,
        },
        {
            "dx": -4,
            "dy": 6,
            "largura": 5,
            "profundidade": 3,
            "sprite": "village_house_moss",
            "rota_horizontal": True,
        },
    )

    def _montar_vila(self, clareira):
        """Monta um pequeno vilarejo determinístico em volta da praça."""
        cx, cy = clareira.centro
        area_sem_arvores = set()
        for layout in self._LAYOUTS_CASA:
            casa_x = cx + layout["dx"]
            casa_y = cy + layout["dy"]
            area_sem_arvores |= self._construir_casa(
                casa_x,
                casa_y,
                largura=layout["largura"],
                profundidade=layout["profundidade"],
                sprite=layout["sprite"],
            )
            area_sem_arvores |= self._pintar_acesso_casa(
                (casa_x, casa_y + 1),
                clareira.centro,
                horizontal_primeiro=layout["rota_horizontal"],
            )

        self._remover_arvores(area_sem_arvores)
        self.pontos_interesse.append(PontoInteresse("vila", cx, cy))

    def _construir_casa(self, ancora_x, ancora_y, largura, profundidade, sprite):
        """Pinta a fundação sólida e ancora nela um sprite de casa completo."""
        if largura < 3 or largura % 2 == 0 or profundidade < 2:
            raise ValueError("a casa precisa de largura ímpar e footprint válido")

        metade = largura // 2
        esquerda = ancora_x - metade
        direita = ancora_x + metade
        topo = ancora_y - profundidade + 1
        area_livre = {
            (x, y)
            for y in range(ancora_y - 6, ancora_y + 3)
            for x in range(esquerda - 2, direita + 3)
            if self.mapa.obter_tile(x, y)
        }

        # Prepara o lote inteiro que aparece atrás do sprite. Isso remove
        # pedras, muros de ruína e arbustos cuja âncora ficava fora da antiga
        # fundação, mas cuja imagem cobria o telhado ou a fachada.
        for x, y in area_livre:
            tile = self.mapa.obter_tile(x, y)
            if not tile or tile.tipo == "deep_water":
                continue
            if tile.bioma == "vila" and tile.bloqueado:
                continue
            if tile.tipo in {"parede", "rubble", "rocha"}:
                tile.tipo = "terra"
            tile.bloqueado = False
            tile.decoracao = None
            tile.bioma = "vila"

        fundacao = set()

        for y in range(topo, ancora_y + 1):
            for x in range(esquerda, direita + 1):
                tile = self.mapa.obter_tile(x, y)
                if not tile:
                    continue
                # A clareira é escolhida longe de água; ainda assim, pintar a
                # fundação inteira evita casas faltando pedaços na borda de um
                # bioma ou após futuras mudanças no gerador.
                tile.tipo = "terra"
                tile.bloqueado = True
                tile.decoracao = None
                tile.bioma = "vila"
                fundacao.add((x, y))

        # Caso a trilha procedural tenha chegado por este quadrante, ela passa
        # a contornar a fundação. Manter o tile bloqueado dentro de
        # ``trilha_tiles`` quebrava tanto o debug quanto a rota até a praça.
        trilhas_interrompidas = fundacao.intersection(self.trilha_tiles)
        self.trilha_tiles.difference_update(fundacao)
        desvio = set()
        if trilhas_interrompidas:
            contorno = {
                *((x, topo - 1) for x in range(esquerda - 1, direita + 2)),
                *((x, ancora_y + 1) for x in range(esquerda - 1, direita + 2)),
                *((esquerda - 1, y) for y in range(topo, ancora_y + 1)),
                *((direita + 1, y) for y in range(topo, ancora_y + 1)),
            }
            for x, y in contorno:
                tile = self.mapa.obter_tile(x, y)
                if not tile or tile.tipo == "deep_water":
                    continue
                tile.tipo = "terra"
                tile.bloqueado = False
                tile.decoracao = None
                tile.bioma = "vila"
                self.trilha_tiles.add((x, y))
                desvio.add((x, y))

        ancora = self.mapa.obter_tile(ancora_x, ancora_y)
        if ancora:
            ancora.decoracao = sprite

        # A soleira fica fora da colisão da construção e dá ao jogador um
        # ponto inequívoco para se aproximar da porta.
        soleira = self.mapa.obter_tile(ancora_x, ancora_y + 1)
        if soleira:
            soleira.tipo = "terra"
            soleira.bloqueado = False
            soleira.decoracao = None
            soleira.bioma = "vila"

        # Copas têm vários tiles de largura. Limpar apenas a fundação deixava
        # árvores com tronco vizinho cobrindo fachadas inteiras.
        return area_livre | desvio

    def _pintar_acesso_casa(self, inicio, destino, horizontal_primeiro=False):
        """Liga a soleira à praça por um caminho ortogonal de terra."""
        x, y = inicio
        destino_x, destino_y = destino
        caminho = [(x, y)]

        def avancar_x():
            nonlocal x
            while x != destino_x:
                x += 1 if destino_x > x else -1
                caminho.append((x, y))

        def avancar_y():
            nonlocal y
            while y != destino_y:
                y += 1 if destino_y > y else -1
                caminho.append((x, y))

        if horizontal_primeiro:
            avancar_x()
            avancar_y()
        else:
            avancar_y()
            avancar_x()

        livres = set()
        for x, y in caminho:
            tile = self.mapa.obter_tile(x, y)
            if not tile or tile.bloqueado or tile.tipo == "deep_water":
                continue
            tile.tipo = "terra"
            tile.bloqueado = False
            tile.decoracao = None
            tile.bioma = "vila"
            self.trilha_tiles.add((x, y))
            livres.add((x, y))
        return livres
