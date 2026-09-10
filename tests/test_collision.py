import math
import unittest

import pygame

from components.combat_system import Projetil
from components.physics import PhysicsComponent


class EmptyParticles:
    def __init__(self):
        self.emissions = []

    def emit(self, *args):
        self.emissions.append(args)


class MapStub:
    def __init__(self, blocked=None, entities=None):
        self.blocked = set(blocked or ())
        self.entidades = list(entities or ())
        self.particulas = EmptyParticles()
        self.efeitos = []

    def is_blocked_terrain(self, x, y):
        return (x, y) in self.blocked


class ProjectileCollisionTests(unittest.TestCase):
    def test_projectile_stops_at_corner_without_curving(self):
        owner = object()
        projectile = Projetil(0.5, 0.5, math.pi / 4, "player", owner, speed=48)
        map_obj = MapStub(blocked={(1, 0), (1, 1)}, entities=[owner])

        projectile.update(1 / 60, map_obj)

        self.assertFalse(projectile.active)
        self.assertAlmostEqual(projectile.x - 0.5, projectile.y - 0.5)

    def test_projectile_uses_targets_real_hitbox(self):
        class Target:
            hp = 10
            x = 1
            y = 0
            hitbox = pygame.Rect(100, 100, 8, 8)

        owner = object()
        target = Target()
        projectile = Projetil(0.5, 0.5, 0, "player", owner, speed=42)
        map_obj = MapStub(entities=[owner, target])

        projectile.update(1 / 60, map_obj)

        self.assertTrue(projectile.active)

    def test_projectile_hit_emits_directional_feedback_and_knockback(self):
        class Physics:
            def __init__(self):
                self.knockback = None

            def move_by(self, dx, dy, distance, map_obj):
                self.knockback = (dx, dy, distance)

        class Target:
            hp = 10
            x = 1
            y = 0
            hitbox = pygame.Rect(31, 12, 18, 18)

            def __init__(self):
                self.physics = Physics()

            def tomar_dano(self, damage, map_obj, critical=False):
                self.hp -= damage

        owner = object()
        target = Target()
        projectile = Projetil(0.5, 0.5, 0, "player", owner, damage=4, speed=42)
        map_obj = MapStub(entities=[owner, target])

        projectile.update(1 / 60, map_obj)

        self.assertFalse(projectile.active)
        self.assertEqual(target.hp, 6)
        self.assertIsNotNone(target.physics.knockback)
        self.assertEqual(len(map_obj.efeitos), 1)
        self.assertEqual(map_obj.particulas.emissions[0][2], "blood")

    def test_guaranteed_critical_uses_multiplier(self):
        class Physics:
            def move_by(self, *args):
                pass

        class Target:
            nome = "Walker"
            hp = 30
            x = 1
            y = 0
            hitbox = pygame.Rect(31, 12, 18, 18)
            physics = Physics()

            def tomar_dano(self, damage, map_obj, critical=False):
                self.hp -= damage

                class Result:
                    absorbed = 0
                    health_damage = damage

                return Result()

        owner = object()
        target = Target()
        projectile = Projetil(
            0.5, 0.5, 0, "player", owner, damage=10, speed=42,
            critical_chance=1.0, critical_multiplier=2.0,
        )
        map_obj = MapStub(entities=[owner, target])

        projectile.update(1 / 60, map_obj)

        self.assertEqual(target.hp, 10)
        self.assertIn("critical", [args[2] for args in map_obj.particulas.emissions])

    def test_projectile_stops_on_tree_without_damage_or_knockback(self):
        class StaticPhysics:
            def move_by(self, *args):
                raise AssertionError("static scenery must not receive knockback")

        class Tree:
            nome = "Carvalho"
            is_static = True
            impact_material = "wood"
            hp = 90
            x = 1
            y = 0
            hitbox = pygame.Rect(31, 12, 18, 18)
            physics = StaticPhysics()

            def tomar_dano(self, *args, **kwargs):
                raise AssertionError("static scenery must not take damage")

        owner = object()
        tree = Tree()
        projectile = Projetil(0.5, 0.5, 0, "player", owner, speed=42)
        map_obj = MapStub(entities=[owner, tree])

        projectile.update(1 / 60, map_obj)

        self.assertFalse(projectile.active)
        self.assertEqual(tree.hp, 90)
        self.assertEqual(map_obj.particulas.emissions[0][2], "wood")

    def test_terrain_impact_uses_material_particles(self):
        class Tile:
            tipo = "deep_water"

        owner = object()
        projectile = Projetil(0.5, 0.5, 0, "player", owner, speed=42)
        map_obj = MapStub(blocked={(1, 0)}, entities=[owner])
        map_obj.obter_tile = lambda x, y: Tile()

        projectile.update(1 / 60, map_obj)

        self.assertFalse(projectile.active)
        self.assertEqual(map_obj.particulas.emissions[0][2], "splash")


class PhysicsCollisionTests(unittest.TestCase):
    def test_touching_tile_edge_is_not_a_collision(self):
        entity = object()
        physics = PhysicsComponent(entity, 0, 0, largura_hb=0.5, altura_hb=0.5)
        map_obj = MapStub(blocked={(1, 0)}, entities=[entity])

        # Esta posição deixa a borda direita exatamente em x=32.
        self.assertFalse(physics.check_collision(0.25, 0, map_obj))

    def test_movement_distance_is_independent_of_frame_rate(self):
        map_obj = MapStub()
        one_frame = PhysicsComponent(object(), 0, 0)
        many_frames = PhysicsComponent(object(), 0, 0)
        one_frame.speed = many_frames.speed = 6.0

        one_frame.move(1, 0, map_obj, 1.0)
        for _ in range(10):
            many_frames.move(1, 0, map_obj, 0.1)

        self.assertAlmostEqual(one_frame.x, many_frames.x)

    def test_speed_multiplier_changes_distance_without_changing_direction(self):
        map_obj = MapStub()
        normal = PhysicsComponent(object(), 0, 0)
        boosted = PhysicsComponent(object(), 0, 0)
        normal.speed = boosted.speed = 4.0

        normal.move(1, 0, map_obj, 0.25)
        boosted.move(1, 0, map_obj, 0.25, speed_multiplier=1.35)

        self.assertAlmostEqual(normal.x, 1.0)
        self.assertAlmostEqual(boosted.x, 1.35)
        self.assertEqual(boosted.y, 0)

    def test_small_corner_overlap_is_nudged_clear(self):
        entity = object()
        physics = PhysicsComponent(entity, 0.20, 0.4375, largura_hb=0.5, altura_hb=0.5)
        map_obj = MapStub(blocked={(1, 0)}, entities=[entity])

        moved = physics.move_by(1, 0, 0.1, map_obj)

        self.assertTrue(moved)
        self.assertGreater(physics.y, 0.4375)

    def test_static_tree_hitbox_covers_full_tile(self):
        class TreeEntity:
            is_static = True
            tags = ("tree",)

        tree = TreeEntity()
        physics = PhysicsComponent(tree, 4, 7)
        self.assertEqual(physics.hitbox, pygame.Rect(4 * 32, 7 * 32, 32, 32))

    def test_melee_damages_static_tree_without_knockback(self):
        from types import SimpleNamespace
        from components.combat_system import executar_golpe_espada

        class StaticPhysics:
            def move_by(self, *args):
                raise AssertionError("static tree must not receive knockback")

        class TreeTarget:
            is_static = True
            impact_material = "wood"
            hp = 50
            x = 2
            y = 1
            hitbox = pygame.Rect(64, 32, 32, 32)
            physics = StaticPhysics()

            def tomar_dano(self, amount, *args, **kwargs):
                self.hp -= amount
                return SimpleNamespace(health_damage=amount, absorbed=0)

        class Attacker:
            x = 1.2
            y = 1.0
            dano = 10

        tree = TreeTarget()
        attacker = Attacker()
        map_obj = MapStub(entities=[attacker, tree])

        hit = executar_golpe_espada(attacker, 2.0, 1.0, map_obj, damage=20)
        self.assertTrue(hit)
        self.assertEqual(tree.hp, 30)
        self.assertEqual(map_obj.particulas.emissions[0][2], "wood")


if __name__ == "__main__":
    unittest.main()
