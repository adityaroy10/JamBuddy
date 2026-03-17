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

    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float, intensity: float = 0.5) -> List[LineEvent]:
        root = _root_midi(chord)
        is_minor = "m" in chord
        offsets = MINOR_OFFSETS if is_minor else MAJOR_OFFSETS
        
        # 1. Dynamic Intensity (velocity scaling)
        base_vel = int(50 + 60 * intensity)
        
        # 2. Rhythm & Fills complexity based on intensity
        # One short phrase every 2 beats, or every beat if intense
        trigger_modulo = 1 if intensity > 0.7 else 2
        if int(beat_position) % trigger_modulo != 0:
            return []
            
        # 3. Micro-timing / Swing implicit in variable duration patterns
        events: List[LineEvent] = []
        num_notes = 4 if intensity > 0.5 else 3
        
        # Sometimes reverse arpeggio for variety
        import random
        if random.random() > 0.5:
            offsets = list(reversed(offsets[:num_notes]))
        else:
            offsets = offsets[:num_notes]
            
        for i, off in enumerate(offsets):
            note = root + off
            if note > 84:
                note -= 12
            # Swing note durations for micro-timing
            dur = 1.0 if not (i % 2 == 0) else 1.2
            if intensity < 0.4:
                dur *= 1.5 # stretch out softly
                
            events.append((note, max(10, min(127, base_vel + random.randint(-5, 5))), dur))
            
        return events

    def reset(self) -> None:
        self._last_beat = -1.0
