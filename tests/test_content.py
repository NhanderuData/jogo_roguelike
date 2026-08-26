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
        self.assertEqual(catalog.weapons["shotgun"].pellets, 6)
        self.assertEqual(catalog.entities["Arvore"].sprite, "tree")
        self.assertEqual(catalog.entities["RedTree"].sprite, "red_tree")

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


if __name__ == "__main__":
    unittest.main()
