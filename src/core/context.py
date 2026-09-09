from __future__ import annotations

from dataclasses import dataclass, field

from core.content import ContentCatalog
from core.audio import AudioService, NullSoundManager
from core.input_manager import InputManager


@dataclass
class GameContext:
    """Services and application state shared by scenes."""

    input: InputManager
    content: ContentCatalog
    audio: AudioService = field(default_factory=NullSoundManager)
    quit_requested: bool = False
    debug_enabled: bool = False

    def request_quit(self) -> None:
        self.quit_requested = True
