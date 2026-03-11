"""
ReaLchords (realjam) accompaniment adapter.
Uses the realjam server's POST /play API for AI chord generation.
When the server is not running or realjam is not installed, falls back to rule-based.
"""
import logging
from typing import List, Any

from .interface import AccompanimentInterface, ChordEvent
from .rule_based import RuleBasedAccompaniment, _chord_notes

logger = logging.getLogger(__name__)

# realjam uses 4 frames per beat
FRAME_PER_BEAT = 4

# Default server URL (run realjam-start-server first, or we can start it)
DEFAULT_REALJAM_URL = "http://127.0.0.1:8080"


def _note_info(pitch: int, frame: int, on: bool) -> dict:
    return {"pitch": pitch, "frame": frame, "on": on}


def _chord_info_to_events(chord_info: Any) -> List[ChordEvent]:
    """ChordInfo is (name: str, midi_notes: List[int], is_bass: bool). Convert to our ChordEvent list."""
    if not chord_info:
        return []
    if isinstance(chord_info, (list, tuple)) and len(chord_info) >= 2:
        name, midi_notes = chord_info[0], chord_info[1]
    else:
        return []
    if isinstance(midi_notes, list) and len(midi_notes) >= 2:
        return [(n, 80, 2.0) for n in midi_notes]
    notes = _chord_notes(str(name)) if name else [60, 64, 67]
    return [(n, 80, 2.0) for n in notes]


class RealJamAccompaniment(AccompanimentInterface):
    """
    AI accompaniment via ReaLchords (realjam server).
    Run `realjam-start-server` in a separate terminal, then use this backend.
    Falls back to rule-based if the server is unavailable.
    """

    def __init__(self, server_url: str = DEFAULT_REALJAM_URL):
        self.server_url = server_url.rstrip("/")
        self.play_url = f"{self.server_url}/play"
        self.fallback = RuleBasedAccompaniment()
        # Session state for realjam API
        self._notes: List[dict] = []
        self._chord_tokens: List[int] = []
        self._frame = 0
        self._intro_set = False
        self._silence_till = 8 * FRAME_PER_BEAT  # 8 beats of silence before AI starts

    def reset(self) -> None:
        self._notes = []
        self._chord_tokens = []
        self._frame = 0
        self._intro_set = False
        self.fallback.reset()

    def generate(self, chord: str, tempo: float, melody_notes: List[int], beat_position: float) -> List[ChordEvent]:
        try:
            import requests
        except ImportError:
            return self.fallback.generate(chord, tempo, melody_notes, beat_position)

        # Current frame index (time in frames)
        frame = int(beat_position * FRAME_PER_BEAT)
        if frame > self._frame:
            self._frame = frame

        # Append current melody as note events (onset now, offset next frame)
        for pitch in melody_notes:
            if 0 <= pitch <= 127:
                self._notes.append(_note_info(pitch, self._frame, on=True))
                self._notes.append(_note_info(pitch, self._frame + 1, on=False))

        payload = {
            "model": "ReaLchords",
            "notes": self._notes,
            "chordTokens": self._chord_tokens,
            "frame": self._frame,
            "lookahead": 4,
            "commitahead": 2,
            "temperature": 0.8,
            "silenceTill": self._silence_till,
            "introSet": self._intro_set,
        }

        try:
            r = requests.post(self.play_url, json=payload, timeout=2.0)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            logger.debug("realjam server unavailable (%s), using rule-based", e)
            return self.fallback.generate(chord, tempo, melody_notes, beat_position)

        new_chords = data.get("newChords") or []
        new_chord_tokens = data.get("newChordTokens") or []
        intro_chord_tokens = data.get("introChordTokens")

        if intro_chord_tokens is not None:
            self._chord_tokens[: self._frame] = intro_chord_tokens
            self._intro_set = True
        if new_chord_tokens:
            self._chord_tokens = self._chord_tokens[: self._frame] + new_chord_tokens

        if not new_chords:
            return self.fallback.generate(chord, tempo, melody_notes, beat_position)

        # Use first chord from this batch
        first = new_chords[0]
        events = _chord_info_to_events(first)
        if not events:
            return self.fallback.generate(chord, tempo, melody_notes, beat_position)
        return events