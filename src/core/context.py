from __future__ import annotations

from dataclasses import dataclass, field

from core.content import ContentCatalog
from core.audio import SoundManager
from core.input_manager import InputManager


@dataclass
class GameContext:
    """Services and application state shared by scenes."""

    input: InputManager
    content: ContentCatalog
    audio: SoundManager = field(default_factory=SoundManager)
    quit_requested: bool = False

    def request_quit(self) -> None:
        self.quit_requested = True
