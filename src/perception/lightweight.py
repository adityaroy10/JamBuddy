"""
Lightweight perception: librosa pitch/onset/beat + simple chord detection.
Kept behind PerceptionInterface so a trained chord/melody model can replace this later.
"""
import warnings
import numpy as np
from .interface import PerceptionInterface, SymbolicStream

# Chord templates: root index 0..11 = C, C#, D, ... B; simple major/minor
CHORD_NAMES = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]


class LightweightPerception(PerceptionInterface):
    def __init__(self, sample_rate: int = 44100, hop_length: int = 512):
        self.sample_rate = sample_rate
        self.hop_length = hop_length
        self._last_chord = "C"
        self._last_tempo = 120.0
        self._buffer: list = []

    def process(self, audio_chunk: bytes, sample_rate: int) -> SymbolicStream:
        try:
            import librosa
        except ImportError:
            return SymbolicStream(chord=self._last_chord, tempo=self._last_tempo)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*n_fft=1024 is too large for input signal.*")

            # Convert bytes to float mono
            buf = np.frombuffer(audio_chunk, dtype=np.int16)
            if buf.size == 0:
                return SymbolicStream(chord=self._last_chord, tempo=self._last_tempo)
            y = buf.astype(np.float32) / 32768.0

            self._buffer.append(y)
            # Process in slightly larger blocks for librosa (e.g. ~2048 samples)
            min_len = 2048
            if sum(len(b) for b in self._buffer) < min_len:
                return SymbolicStream(chord=self._last_chord, tempo=self._last_tempo)

            y_block = np.concatenate(self._buffer)
            self._buffer = [y_block[min_len:]] if len(y_block) > min_len else []

            if len(y_block) < min_len:
                return SymbolicStream(chord=self._last_chord, tempo=self._last_tempo)

            y_block = y_block[:min_len * 2]  # cap for speed

            # Tempo/beat
            try:
                tempo, beat_frames = librosa.beat.beat_track(y=y_block, sr=sample_rate, hop_length=self.hop_length)
                if np.isscalar(tempo):
                    self._last_tempo = float(np.clip(tempo, 60, 180))
                else:
                    self._last_tempo = 120.0
            except Exception:
                self._last_tempo = 120.0

            # Pitch (monophonic estimate) -> melody note
            melody_notes: list = []
            try:
                f0, voiced_flag, _ = librosa.pyin(
                    y_block, fmin=librosa.note_to_hz("E2"), fmax=librosa.note_to_hz("E6"),
                    sr=sample_rate, hop_length=self.hop_length
                )
                if voiced_flag is not None and np.any(voiced_flag):
                    midx = np.nanargmax(np.nanmean(f0) if np.any(~np.isnan(f0)) else 0)
                    if not np.isnan(f0).all():
                        hz = np.nanmedian(f0[voiced_flag])
                        if 80 <= hz <= 1000:
                            midi = int(round(69 + 12 * np.log2(hz / 440)))
                            midi = max(40, min(84, midi))
                            melody_notes = [midi]
            except Exception:
                pass

            # Simple chord from spectrum (root + major/minor)
            try:
                chroma = librosa.feature.chroma_cqt(y=y_block, sr=sample_rate, hop_length=self.hop_length)
                chroma_med = np.median(chroma, axis=1)
                root = int(np.argmax(chroma_med))
                # crude major vs minor from third
                third = (root + 4) % 12
                fifth = (root + 7) % 12
                minor_third = (root + 3) % 12
                if chroma_med[minor_third] > chroma_med[third]:
                    chord = f"{CHORD_NAMES[root]}m"
                else:
                    chord = CHORD_NAMES[root]
                self._last_chord = chord
            except Exception:
                chord = self._last_chord

            return SymbolicStream(
                chord=chord,
                melody_notes=melody_notes,
                beat_position=0.0,
                tempo=self._last_tempo,
                chord_confidence=0.7,
            )

    def reset(self) -> None:
        self._buffer.clear()
        self._last_chord = "C"
        self._last_tempo = 120.0
