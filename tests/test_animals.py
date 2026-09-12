import math
import unittest
import pygame

from core.content import ContentCatalog
from core.context import GameContext
from core.input_manager import InputManager
from entities.actor import Entidade
from graphics import recursos
from map.map_gen import Mapa

ALL_ANIMALS = [
    ("Touro", "animal_bull", "territorial"),
    ("Bezerro", "animal_calf", "flee"),
    ("Pintinho", "animal_chick", "flee"),
    ("Cordeiro", "animal_lamb", "flee"),
    ("Porquinho", "animal_piglet", "flee"),
    ("Galo", "animal_rooster", "flee"),
    ("Ovelha", "animal_sheep", "flee"),
    ("Peru", "animal_turkey", "flee"),
    ("Javali", "animal_boar", "territorial"),
    ("Cervo", "animal_deer", "flee"),
    ("Raposa", "animal_fox", "territorial"),
    ("Lebre", "animal_hare", "flee"),
    ("Galo Silvestre", "animal_black_grouse", "flee"),
]


class AnimalValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        recursos.carregar_tudo()
        cls.catalog = ContentCatalog.load_default()
        cls.context = GameContext(
            input=InputManager(),
            content=cls.catalog,
        )

    def test_all_13_animals_exist_in_catalog(self):
        self.assertEqual(len(ALL_ANIMALS), 13)
        for name, sprite_key, ai_mode in ALL_ANIMALS:
            with self.subTest(animal=name):
                self.assertIn(name, self.catalog.entities)
                definition = self.catalog.entities[name]
                self.assertEqual(definition.role, "animal")
                self.assertEqual(definition.ai_mode, ai_mode)
                self.assertEqual(definition.sprite, sprite_key)
                self.assertTrue(definition.has_ai)
                self.assertGreater(definition.hp, 0)
                self.assertGreater(definition.speed, 0)
                self.assertTrue(len(definition.loot) > 0)
                self.assertIn("Carne Crua", definition.loot)

    def test_all_13_animal_sprites_loaded_with_all_directions(self):
        directions = ["down", "up", "left", "right"]
        states = ["idle", "move"]

        for name, sprite_key, _ in ALL_ANIMALS:
            with self.subTest(animal=name, sprite=sprite_key):
                self.assertIn(sprite_key, recursos.SPRITES)
                anim_data = recursos.SPRITES[sprite_key]
                self.assertIsInstance(anim_data, dict)

                for state in states:
                    self.assertIn(state, anim_data)
                    for d in directions:
                        self.assertIn(d, anim_data[state])
                        frames = anim_data[state][d]
                        self.assertIsInstance(frames, list)
                        self.assertGreaterEqual(
                            len(frames),
                            4,
                            f"{name} {state} {d} must have at least 4 frames",
                        )
                        for idx, frame in enumerate(frames):
                            self.assertIsInstance(frame, pygame.Surface)
                            w, h = frame.get_size()
                            self.assertGreater(w, 0)
                            self.assertGreater(h, 0)

    def test_all_13_animals_instantiate_and_animate(self):
        for name, sprite_key, _ in ALL_ANIMALS:
            with self.subTest(animal=name):
                ent = Entidade(10.0, 10.0, name, self.context)
                self.assertEqual(ent.nome, name)
                self.assertEqual(ent.role, "animal")
                self.assertIsNotNone(ent.sprite.image)

                # Test idle animation update
                ent.physics.moving = False
                ent.update(0.1, None)
                self.assertIsNotNone(ent.sprite.image)

                # Test directional movement animation
                for dx, dy, expected_dir in [
                    (1, 0, "right"),
                    (-1, 0, "left"),
                    (0, 1, "down"),
                    (0, -1, "up"),
                ]:
                    ent.physics.set_direction = getattr(ent.sprite, "set_direction", None)
                    if ent.physics.set_direction:
                        ent.physics.set_direction(dx, dy)
                    ent.physics.moving = True
                    ent.update(0.1, None)
                    self.assertEqual(ent.sprite.direction, expected_dir)
                    self.assertIsNotNone(ent.sprite.image)

    def test_fleeing_animals_flee_from_player(self):
        flee_animals = [a for a in ALL_ANIMALS if a[2] == "flee"]
        for name, _, _ in flee_animals:
            with self.subTest(animal=name):
                world = Mapa(self.context, seed=10)
                # Position player at (20, 20) and animal at (22, 20) - distance is 2 tiles
                world.jogador.x, world.jogador.y = 20.0, 20.0
                animal = Entidade(22.0, 20.0, name, self.context)
                initial_x = animal.x
                # Update AI
                animal.ai.update(world, 0.2)
                # Animal should have moved further to the right (fleeing player at x=20)
                self.assertGreater(
                    animal.x,
                    initial_x,
                    f"{name} should flee away from player",
                )

    def test_territorial_animals_defend_when_hurt(self):
        territorial_animals = [a for a in ALL_ANIMALS if a[2] == "territorial"]
        for name, _, _ in territorial_animals:
            with self.subTest(animal=name):
                world = Mapa(self.context, seed=15)
                world.jogador.x, world.jogador.y = 30.0, 30.0
                # Animal at (35, 30) - 5 tiles away (outside peaceful trigger)
                animal = Entidade(35.0, 30.0, name, self.context)
                # Hurt animal to provoke it
                animal.combat.hp = animal.combat.hp_max - 5
                initial_x = animal.x
                # Update AI
                animal.ai.update(world, 0.2)
                # Provoked territorial animal moves towards player (towards x=30)
                self.assertLess(
                    animal.x,
                    initial_x,
                    f"{name} should charge towards player when hurt",
                )

    def test_killing_animal_drops_meat(self):
        world = Mapa(self.context, seed=20)
        animal = Entidade(15.0, 15.0, "Ovelha", self.context)
        world.entidades.append(animal)
        initial_loot_count = len(world.items_no_chao)

        # Inflict lethal damage
        animal.tomar_dano(animal.hp_max + 10, world)
        self.assertEqual(animal.hp, 0)

        # Simulation resolves death and drops loot
        world.simulation.update(0.1)
        self.assertGreater(len(world.items_no_chao), initial_loot_count)
        dropped_item = world.items_no_chao[-1]
        self.assertIn(dropped_item.item_name, ["Carne Crua", "Couro"])

    def test_world_spawns_both_farm_and_wild_animals(self):
        world = Mapa(self.context, seed=99)
        farm_names = {a[0] for a in ALL_ANIMALS if a[1].startswith("animal_") and a[0] in [
            "Touro", "Bezerro", "Pintinho", "Cordeiro", "Porquinho", "Galo", "Ovelha", "Peru"
        ]}
        hunt_names = {a[0] for a in ALL_ANIMALS if a[0] in [
            "Javali", "Cervo", "Raposa", "Lebre", "Galo Silvestre"
        ]}

        spawned_names = {ent.nome for ent in world.entidades if getattr(ent, "role", None) == "animal"}
        spawned_farm = spawned_names.intersection(farm_names)
        spawned_hunt = spawned_names.intersection(hunt_names)

        self.assertGreater(len(spawned_farm), 0, "World should spawn farm animals")
        self.assertGreater(len(spawned_hunt), 0, "World should spawn wild animals")

    def test_animal_sprite_proportions_not_tiny(self):
        """Regression test: all animals must have proper pixel dimensions relative to the 2x world."""
        min_heights = {
            "animal_bull": 60,
            "animal_calf": 40,
            "animal_deer": 55,
            "animal_boar": 45,
            "animal_sheep": 40,
            "animal_piglet": 28,
            "animal_turkey": 26,
            "animal_fox": 32,
            "animal_hare": 28,
            "animal_rooster": 22,
            "animal_lamb": 28,
            "animal_black_grouse": 26,
            "animal_chick": 16,
        }
        for _, sprite_key, _ in ALL_ANIMALS:
            with self.subTest(animal_sprite=sprite_key):
                self.assertIn(sprite_key, recursos.SPRITES)
                frame = recursos.SPRITES[sprite_key]["idle"]["down"][0]
                bb = frame.get_bounding_rect()
                expected_min = min_heights.get(sprite_key, 20)
                self.assertGreaterEqual(
                    bb.height,
                    expected_min,
                    f"{sprite_key} is too small! Height {bb.height}px < expected {expected_min}px",
                )


if __name__ == "__main__":
    unittest.main()
