import math
import unittest

from components.ai import AIComponent
from map.map_gen import Mapa


class MockPhysics:
    def __init__(self, speed=2.0):
        self.speed = speed
        self.x = 0.0
        self.y = 0.0
        self.last_move_dir = (0.0, 0.0)
        self.move_count = 0

    def move(self, dx, dy, mapa_obj, dt):
        self.last_move_dir = (dx, dy)
        self.move_count += 1
        return True

    def check_collision(self, *args):
        return False


class MockCombat:
    def __init__(self, hp=100, hp_max=100):
        self.hp = hp
        self.hp_max = hp_max
        self.dead = False

    def take_damage(self, amount, mapa_obj):
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.dead = True


class MockEntity:
    def __init__(self, x, y, role="enemy", ai_mode="chase", name="Orc"):
        self.x = float(x)
        self.y = float(y)
        self.role = role
        self.ai_mode = ai_mode
        self.nome = name
        self.hp = 100
        self.hp_max = 100
        self.is_static = False
        self.physics = MockPhysics()
        self.combat = MockCombat(100, 100)
        self.ai = AIComponent(self)
        self.shots = 0
        self.melee_attacks = 0

    def atirar(self, tx, ty, mapa_obj):
        self.shots += 1

    def atacar_espada(self, tx, ty, mapa_obj):
        self.melee_attacks += 1


class MockPlayer:
    def __init__(self, x=10.0, y=10.0):
        self.x = float(x)
        self.y = float(y)
        self.role = "player"
        self.hp = 100
        self.hp_max = 100
        self.is_static = False


class MockMap:
    def __init__(self, player=None):
        self.jogador = player or MockPlayer()
        self.entidades = []

    def is_blocked_terrain(self, x, y):
        return False

    def is_near_bonfire(self, x, y, radius=4.5):
        return False

    def get_nearest_bonfire(self, x, y):
        return None

    def alert_enemies(self, origin_x: float, origin_y: float, radius: float = 18.0):
        Mapa.alert_enemies(self, origin_x, origin_y, radius)

    def alert_allies(self, caller, radius: float = 7.0):
        Mapa.alert_allies(self, caller, radius)


class AIImprovementsTests(unittest.TestCase):
    def test_flocking_separation_deflects_overlapping_allies(self):
        """Dois inimigos com o mesmo papel se repelem para evitar a fila indiana (conga line)."""
        e1 = MockEntity(10.0, 10.0, role="enemy")
        e2 = MockEntity(10.5, 10.0, role="enemy")  # Vizinho logo à direita

        world = MockMap()
        world.entidades = [e1, e2]

        # Quer se mover para a direita (1, 0) em direção ao jogador
        base_dir_x, base_dir_y = 1.0, 0.0
        sep_x, sep_y = e1.ai._apply_flocking_separation(world, base_dir_x, base_dir_y, radius=1.4)

        # Como e2 está à direita, e1 deve ser empurrado para longe de e2 (para a esquerda ou desviado)
        # O vetor resultante deve ter uma componente x reduzida ou negativa em relação ao vetor original
        self.assertLess(sep_x, base_dir_x, "A separação de boids deve afastar o inimigo do aliado à sua frente")

    def test_ranged_kiting_retreats_when_player_too_close(self):
        """Inimigo à distância (ranged/hybrid) recua se o jogador chegar muito perto (< 2.8 tiles)."""
        player = MockPlayer(10.0, 10.0)
        # Runner está a 1.5 tiles à direita do jogador (x=11.5)
        runner = MockEntity(11.5, 10.0, role="enemy", ai_mode="ranged", name="Orc Rogue")
        world = MockMap(player)
        world.entidades = [runner]

        runner.ai.update(world, 0.1)

        # Ele deve ter se movido para a direita (afastando-se do jogador em x=10.0)
        last_dx, last_dy = runner.physics.last_move_dir
        self.assertGreater(last_dx, 0.0, "Inimigo ranged deve recuar do jogador quando próximo")

    def test_herd_panic_propagation(self):
        """Ao assustar ou ferir um membro do rebanho, os outros animais da mesma espécie entram em pânico."""
        sheep1 = MockEntity(10.0, 10.0, role="animal", ai_mode="flee", name="Ovelha")
        sheep2 = MockEntity(12.0, 10.0, role="animal", ai_mode="flee", name="Ovelha")  # Próxima (2 tiles)
        sheep_far = MockEntity(35.0, 35.0, role="animal", ai_mode="flee", name="Ovelha")  # Longe (35 tiles)
        boar = MockEntity(11.0, 10.0, role="animal", ai_mode="territorial", name="Javali")  # Outra espécie

        world = MockMap()
        world.entidades = [sheep1, sheep2, sheep_far, boar]

        # Alerta o rebanho a partir de sheep1
        sheep1.ai._alert_nearby_herd(world, radius=7.0)

        # sheep2 deve ter recebido panic_timer
        self.assertGreater(sheep2.ai.panic_timer, 0.0, "Ovelha próxima deve receber alerta de pânico")
        # sheep_far NÃO deve receber
        self.assertEqual(sheep_far.ai.panic_timer, 0.0, "Ovelha distante não deve ser alertada")
        # boar (outra espécie) NÃO deve receber
        self.assertEqual(boar.ai.panic_timer, 0.0, "Outra espécie não deve compartilhar alarme de rebanho")

    def test_territorial_charge_activation(self):
        """Animal territorial (como Javali) desfere investida rápida em linha reta quando provocado."""
        player = MockPlayer(10.0, 10.0)
        # Javali a 4 tiles de distância, ferido
        boar = MockEntity(14.0, 10.0, role="animal", ai_mode="territorial", name="Javali")
        boar.combat.hp = 50
        boar.combat.hp_max = 100

        world = MockMap(player)
        world.entidades = [boar]

        # Atualização do IA deve engatilhar a investida (charge_timer > 0)
        boar.ai.charge_cooldown = 0.0
        boar.ai.update(world, 0.1)

        self.assertGreater(boar.ai.charge_timer, 0.0, "Javali ferido em distância de ataque deve engatilhar investida")
        # Direção da investida deve apontar para o jogador (dx < 0, já que jogador está em x=10 e javali em x=14)
        charge_x, charge_y = boar.ai.charge_dir
        self.assertLess(charge_x, 0.0, "Investida deve apontar na direção do jogador")

    def test_gunshot_alerts_distant_enemies(self):
        """Disparo de arma de fogo acorda e alerta inimigos num raio amplo (18 tiles)."""
        player = MockPlayer(10.0, 10.0)
        # Inimigo a 12 tiles (fora de visão direta comum, mas dentro do raio auditivo de 18 tiles)
        enemy = MockEntity(22.0, 10.0, role="enemy", ai_mode="chase", name="Orc Warrior")
        far_enemy = MockEntity(50.0, 50.0, role="enemy", ai_mode="chase", name="Orc Shaman")

        world = MockMap(player)
        world.entidades = [enemy, far_enemy]

        # Simula som de tiro disparado na posição do player
        world.alert_enemies(player.x, player.y, radius=18.0)

        # enemy deve investigar o local do tiro
        self.assertEqual(enemy.ai.idle_state, "investigate")
        self.assertEqual(enemy.ai.investigate_pos, (player.x, player.y))
        self.assertGreater(enemy.ai.investigate_timer, 0.0)

        # far_enemy (distância ~56 tiles) não deve ter escutado
        self.assertNotEqual(far_enemy.ai.idle_state, "investigate")

    def test_stalker_prowl_and_pounce(self):
        """Stalker Noturno alterna entre rondar na escuridão e desferir o bote (pounce)."""
        player = MockPlayer(10.0, 10.0)
        # Stalker a 6.0 tiles de distância (zona de espreita entre 4.8 e 9.5 tiles)
        stalker = MockEntity(16.0, 10.0, role="enemy", ai_mode="stalker", name="Stalker Noturno")
        world = MockMap(player)
        world.entidades = [stalker]

        # Configura o timer de espreita para expirar e disparar o bote
        stalker.ai.stalk_timer = 0.0
        stalker.ai.pounce_timer = 0.0
        stalker.ai.update(world, 0.1)

        # Deve ter ativado o bote súbito com pounce_timer > 0
        self.assertGreater(stalker.ai.pounce_timer, 0.0, "Stalker deve acionar o bote ao concluir a espreita")


if __name__ == "__main__":
    unittest.main()
