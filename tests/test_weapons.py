import unittest

from components.combat import CombatComponent
from components.inventory import InventoryComponent
from components.weapons import WeaponComponent
from core.content import ContentCatalog


class SilentAudio:
    def __init__(self):
        self.played = []

    def play(self, name, volume=1.0):
        self.played.append(name)


class WeaponTests(unittest.TestCase):
    def setUp(self):
        self.content = ContentCatalog.load_default()

        class Owner:
            pass

        self.owner = Owner()
        self.owner.inventory = InventoryComponent(self.content)
        self.owner.inventory.add_item("Munição 9mm", 2)
        self.owner.inventory.add_item("Cartuchos calibre 12", 2)
        self.audio = SilentAudio()
        self.weapons = WeaponComponent(self.owner, self.content, self.audio)
        self.owner.weapons = self.weapons

    def test_selects_unlocked_2d_weapon_slot(self):
        self.assertEqual(
            self.weapons.slot_order,
            ("pistol_glock17", "shotgun_remington870", "smg_mp5", "machete", "flamethrower", "rpg"),
        )
        self.assertTrue(self.weapons.select_slot(1))
        self.assertEqual(self.weapons.current_id, "shotgun_remington870")
        self.assertEqual(self.weapons.current.sprite, "weapon_shotgun_remington870")

    def test_reload_moves_reserve_ammo_into_magazine(self):
        self.weapons.magazines["pistol_glock17"] = 2
        reserve_before = self.owner.inventory.ammo_count("9mm")

        self.assertTrue(self.weapons.start_reload())
        self.weapons.update(self.weapons.current.reload_time)

        self.assertEqual(self.weapons.magazines["pistol_glock17"], 17)
        self.assertEqual(self.owner.inventory.ammo_count("9mm"), reserve_before - 15)

    def test_unlock_rejects_duplicate_weapon(self):
        self.assertFalse(self.weapons.unlock("shotgun_remington870"))
        self.assertTrue(self.weapons.unlock("rifle_ak47"))
        self.assertEqual(self.weapons.current_id, "rifle_ak47")


class ArmorTests(unittest.TestCase):
    def test_armor_absorbs_damage_before_health(self):
        class Entity:
            pass

        entity = Entity()
        combat = CombatComponent(entity, hp_max=100, damage=1)
        combat.add_armor(20)
        combat.take_damage(15)

        self.assertEqual(combat.armor, 5)
        self.assertEqual(combat.hp, 100)

    def test_damage_result_reports_partial_armor_absorption(self):
        class Entity:
            pass

        entity = Entity()
        combat = CombatComponent(entity, hp_max=100, damage=1)
        combat.add_armor(6)

        result = combat.take_damage(10)

        self.assertEqual(result.absorbed, 6)
        self.assertEqual(result.health_damage, 4)
        self.assertEqual(combat.hp, 96)


if __name__ == "__main__":
    unittest.main()
