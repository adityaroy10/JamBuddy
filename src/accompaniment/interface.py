"""
Accompaniment interface: symbolic stream -> backing (chords, rhythm).
Implementations: rule_based (now), realjam adapter (later). Training = new backend + config.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple

# MIDI events: (note_number, velocity, duration_16ths)
ChordEvent = Tuple[int, int, float]


class AccompanimentInterface(ABC):
    """Symbolic input -> chord/backing MIDI events."""

    @abstractmethod
    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float) -> List[ChordEvent]:
        """Generate backing chord events (e.g. for current beat). Returns list of (midi_note, velocity, duration_16ths)."""
        pass

    def reset(self) -> None:
        """Reset state for new phrase/song."""
        pass
