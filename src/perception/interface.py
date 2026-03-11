"""
Perception interface: audio -> symbolic (chords, melody, beat).
Implementations: lightweight (librosa + simple chord), or trained model later.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SymbolicStream:
    """Internal format: chord symbols + melody events per time step."""
    # Current chord (e.g. "C", "Am", "Fmaj7")
    chord: str = "C"
    # Melody as MIDI note numbers (e.g. [60, 64, 67] or [] if chord-only)
    melody_notes: List[int] = field(default_factory=list)
    # Beat position (0 = downbeat, 0.25 = 16th, etc.)
    beat_position: float = 0.0
    # Tempo in BPM
    tempo: float = 120.0
    # Confidence 0..1 for chord
    chord_confidence: float = 1.0


class PerceptionInterface(ABC):
    """Abstract perception: raw audio -> SymbolicStream."""

    @abstractmethod
    def process(self, audio_chunk: bytes, sample_rate: int) -> SymbolicStream:
        """Process one chunk of audio; return current symbolic state."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state (e.g. on new song)."""
        pass
