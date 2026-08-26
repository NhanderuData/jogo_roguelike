from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = ASSETS_DIR / "data"


def asset_path(filename: str) -> Path:
    return ASSETS_DIR / filename
