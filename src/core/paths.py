import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_assets_dir() -> Path:
    override = os.environ.get("ROGUE_LLAMA_ASSETS")
    candidates = [
        Path(override).expanduser() if override else None,
        PROJECT_ROOT / "assets",
        Path(sys.prefix) / "share" / "rogue-llama" / "assets",
    ]
    for candidate in candidates:
        if candidate and candidate.is_dir():
            return candidate
    return PROJECT_ROOT / "assets"


ASSETS_DIR = _resolve_assets_dir()
DATA_DIR = ASSETS_DIR / "data"


def asset_path(filename: str) -> Path:
    return ASSETS_DIR / filename
