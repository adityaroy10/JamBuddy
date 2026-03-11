"""
Rule-based accompaniment: chord -> block chords or simple pattern.
Same interface as future realjam adapter: config selects backend.
"""
from typing import List, Tuple

from .interface import AccompanimentInterface, ChordEvent

# Root to MIDI (C4 = 60). Simple triads: root, third, fifth (major or minor)
CHORD_TO_MIDI = {
    "C": (60, 64, 67), "C#": (61, 65, 68), "D": (62, 66, 69), "D#": (63, 67, 70),
    "E": (64, 68, 71), "F": (65, 69, 72), "F#": (66, 70, 73), "G": (67, 71, 74),
    "G#": (68, 72, 75), "A": (69, 73, 76), "A#": (70, 74, 77), "B": (71, 75, 78),
}
CHORD_TO_MIDI_MINOR = {
    "Cm": (60, 63, 67), "C#m": (61, 64, 68), "Dm": (62, 65, 69), "D#m": (63, 66, 70),
    "Em": (64, 67, 71), "Fm": (65, 68, 72), "F#m": (66, 69, 73), "Gm": (67, 70, 74),
    "G#m": (68, 71, 75), "Am": (69, 72, 76), "A#m": (70, 73, 77), "Bm": (71, 74, 78),
}


def _parse_chord(s: str) -> Tuple[str, bool]:
    s = s.strip()
    if s.endswith("m"):
        return s[:-1].replace("#", "#"), True
    return s.replace("#", "#"), False


def _chord_notes(chord: str) -> List[int]:
    root, is_minor = _parse_chord(chord)
    if is_minor:
        notes = CHORD_TO_MIDI_MINOR.get(chord)
    else:
        notes = CHORD_TO_MIDI.get(root)
    if notes is None:
        # fallback: C major
        return [60, 64, 67]
    return list(notes)


class RuleBasedAccompaniment(AccompanimentInterface):
    """Simple block chords on beat; one chord per beat, 2-beat duration."""

    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float) -> List[ChordEvent]:
        notes = _chord_notes(chord)
        # One chord per beat, duration 2 16ths (staccato feel)
        velocity = 80
        duration_16ths = 2.0
        return [(n, velocity, duration_16ths) for n in notes]
