"""
Local Symbolic AI Model (Markov Chain)
Observes the player's chords and learns transition probabilities,
then generates intelligent passing chords and varied rhythms.
"""
from typing import List
import random
from .interface import AccompanimentInterface, ChordEvent
from .rule_based import _chord_notes

class MarkovAccompaniment(AccompanimentInterface):
    def __init__(self):
        self.transitions: dict = {}
        self.last_chord: str | None = None
        self.last_notes: List[int] = []
        self.beat_count: int = 0
        
    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float, intensity: float = 0.5) -> List[ChordEvent]:
        # Learn transition
        if self.last_chord and self.last_chord != chord:
            if self.last_chord not in self.transitions:
                self.transitions[self.last_chord] = {}
            self.transitions[self.last_chord][chord] = self.transitions[self.last_chord].get(chord, 0) + 1
            
        self.last_chord = chord
        self.beat_count += 1
        
        # Decide if we replace the chord with an AI suggestion (e.g., probability based on intensity)
        target_chord = chord
        if intensity > 0.6 and chord in self.transitions and random.random() < 0.3:
            # Pick a learned transition probabilistically
            choices = list(self.transitions[chord].keys())
            weights = list(self.transitions[chord].values())
            if choices:
                target_chord = random.choices(choices, weights=weights)[0]
                
        notes = _chord_notes(target_chord)
        
        # Smooth Voice Leading
        if self.last_notes and len(self.last_notes) == len(notes):
            # Try to map new notes to be as close to previous notes as possible
            # by shifting octaves.
            smoothed_notes = []
            for i, n in enumerate(notes):
                prev_n = self.last_notes[i]
                
                # Shift octave up or down to minimize distance
                best_n = n
                best_dist = abs(n - prev_n)
                
                for shift in [-12, 12]:
                    candidate = n + shift
                    if abs(candidate - prev_n) < best_dist:
                        best_n = candidate
                        best_dist = abs(candidate - prev_n)
                        
                smoothed_notes.append(best_n)
            
            # Sort to keep them in order (low to high)
            notes = sorted(smoothed_notes)
            
        self.last_notes = notes
        
        # AI Rhythm generation for Warm Pads
        # Pads should be sustained mostly. No arpeggiation.
        base_vel = int(60 + 30 * intensity)
        dur = 4.0 # Always sustain for full beat length or longer
        
        # Very gentle velocity variation for pads
        return [
            (n, base_vel + random.randint(-4, 4), dur)
            for n in notes
        ]

    def reset(self) -> None:
        self.last_chord = None
        self.last_notes = []
        self.beat_count = 0
