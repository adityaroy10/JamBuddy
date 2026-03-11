"""
Lines interface: symbolic stream -> short melodic phrases (fills, support).
Implementations: rule_based (now), Magenta/trained later. Same I/O for easy swap.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple

# (midi_note, velocity, duration_16ths)
LineEvent = Tuple[int, int, float]


class LinesInterface(ABC):
    """Chord/melody context -> fill/support line MIDI events."""

    @abstractmethod
    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float) -> List[LineEvent]:
        """Generate one short phrase (fills, licks)."""
        pass

    def reset(self) -> None:
        pass
