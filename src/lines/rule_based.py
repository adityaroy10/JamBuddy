"""
Rule-based lines: chord-tones and simple scale snippets as fills.
Interface matches future Magenta/Improv RNN backend.
"""
from typing import List, Tuple

from .interface import LinesInterface, LineEvent

# Chord tones (scale degrees) for fills: root, 3rd, 5th, octave, 3rd+1
MAJOR_OFFSETS = [0, 4, 7, 12, 16]  # semitones from root
MINOR_OFFSETS = [0, 3, 7, 12, 15]


def _root_midi(chord: str) -> int:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    base = chord.replace("m", "").strip()
    try:
        idx = names.index(base)
    except ValueError:
        idx = 0
    return 60 + idx  # C4


class RuleBasedLines(LinesInterface):
    """Short fill every few beats using chord tones."""

    def __init__(self):
        self._last_beat = -1.0

    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float) -> List[LineEvent]:
        root = _root_midi(chord)
        is_minor = "m" in chord
        offsets = MINOR_OFFSETS if is_minor else MAJOR_OFFSETS
        # One short phrase every 2 beats
        if int(beat_position) % 2 != 0:
            return []
        events: List[LineEvent] = []
        for i, off in enumerate(offsets[:4]):
            note = root + off
            if note > 84:
                note -= 12
            events.append((note, 70, 1.0))
        return events

    def reset(self) -> None:
        self._last_beat = -1.0
