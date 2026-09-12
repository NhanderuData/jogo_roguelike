import json
import tempfile
import unittest
from pathlib import Path

from core.content import ContentCatalog


class ContentCatalogTests(unittest.TestCase):
    def test_default_catalog_loads(self):
        catalog = ContentCatalog.load_default()

        self.assertIn("Bandagem", catalog.items)
        self.assertIn("Survivor", catalog.entities)
        self.assertIn("Bandagem", catalog.entities["Walker"].loot)
        self.assertIn("Energético", catalog.entities["Walker"].loot)
        self.assertGreaterEqual(catalog.weapons["shotgun"].pellets, 6)
        self.assertEqual(catalog.entities["Arvore"].sprite, "tree")
        self.assertTrue(catalog.entities["Arvore"].is_static)
        self.assertIn("tree", catalog.entities["Arvore"].tags)
        self.assertEqual(catalog.entities["Arvore"].role, "prop")
        self.assertEqual(catalog.entities["RedTree"].sprite, "red_tree")
        self.assertFalse(catalog.entities["Walker"].is_static)
        self.assertEqual(catalog.entities["Survivor"].role, "player")
        self.assertEqual(catalog.entities["Runner"].ai_mode, "hybrid")
        self.assertEqual(catalog.entities["Runner"].ranged_interval, 1.25)

    def test_unknown_loot_reference_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "items.json").write_text("{}", encoding="utf-8")
            (directory / "entities.json").write_text(
                json.dumps(
                    {
                        "Enemy": {
                            "hp": 1,
                            "damage": 1,
                            "xp": 1,
                            "speed": 1,
                            "sprite": "enemy",
                            "loot": ["Missing item"],
                        }
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "unknown items"):
                ContentCatalog.from_directory(directory)

    def test_unknown_impact_material_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "items.json").write_text("{}", encoding="utf-8")
            (directory / "entities.json").write_text(
                json.dumps({
                    "Prop": {
                        "hp": 1,
                        "damage": 0,
                        "xp": 0,
                        "speed": 0,
                        "sprite": "prop",
                        "ai": False,
                        "impact_material": "lava",
                    }
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "impact materials"):
                ContentCatalog.from_directory(directory)

    def test_unknown_ai_mode_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "items.json").write_text("{}", encoding="utf-8")
            (directory / "entities.json").write_text(
                json.dumps({
                    "Enemy": {
                        "hp": 1,
                        "damage": 1,
                        "xp": 0,
                        "speed": 1,
                        "sprite": "enemy",
                        "ai_mode": "telepathic",
                    }
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "unknown ai_mode"):
                ContentCatalog.from_directory(directory)


if __name__ == "__main__":
    unittest.main()
