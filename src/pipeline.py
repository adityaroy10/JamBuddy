"""
Pipeline: perception -> accompaniment/lines -> render -> mix with dry.
Runs perception every N blocks to control CPU; fills accompaniment ring buffer.
"""
import numpy as np
import threading
from typing import Optional

from src.config import SAMPLE_RATE, BUFFER_SIZE, get_soundfont_path
from src.perception import LightweightPerception
from src.perception.interface import SymbolicStream
from src.accompaniment import RuleBasedAccompaniment
from src.lines import RuleBasedLines
from src.render import FluidSynthRender


# Modes: both A and B as per plan
MODE_A_SOLO = "solo"           # Solo in -> backing + support lines
MODE_B_CHORDS = "chords"       # Chords in -> lines (AI fills)
MODE_B_VIBE = "chords_vibe"    # Chords + vibe (UI) -> backing (and optionally lines)


class Pipeline:
    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        block_size: int = BUFFER_SIZE,
        mode: str = MODE_A_SOLO,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.mode = mode
        self.dry_gain = 0.9
        self.wet_gain = 0.5

        self.perception = LightweightPerception(sample_rate=sample_rate)
        self.accompaniment = RuleBasedAccompaniment()
        self.lines_gen = RuleBasedLines()
        sf_path = get_soundfont_path()
        self.renderer = FluidSynthRender(sample_rate=sample_rate, soundfont_path=sf_path)

        # Accumulate input for perception (run every N blocks)
        self._input_accum = np.array([], dtype=np.float32)
        self._blocks_until_perceive = 0
        self._perceive_every_n_blocks = max(4, 2048 // block_size)  # ~2048 samples

        # Latest symbolic state (thread-safe)
        self._symbolic: Optional[SymbolicStream] = None
        self._lock = threading.Lock()

        # Pre-rendered accompaniment: (samples array, read index)
        self._accomp_samples: np.ndarray = np.zeros(0, dtype=np.float32)
        self._accomp_index: int = 0

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.perception.reset()
        self.accompaniment.reset()
        self.lines_gen.reset()

    def _run_perception(self, audio_float: np.ndarray) -> SymbolicStream:
        if audio_float.size == 0:
            with self._lock:
                s = self._symbolic
            return s or SymbolicStream()
        raw = (np.clip(audio_float, -1, 1) * 32767).astype(np.int16).tobytes()
        stream = self.perception.process(raw, self.sample_rate)
        with self._lock:
            self._symbolic = stream
        return stream

    def _generate_and_render(self, stream: SymbolicStream) -> None:
        backing: list = []
        lines: list = []
        if self.mode == MODE_A_SOLO:
            backing = self.accompaniment.generate(
                stream.chord, stream.tempo, stream.melody_notes, stream.beat_position
            )
            lines = self.lines_gen.generate(
                stream.chord, stream.tempo, stream.melody_notes, stream.beat_position
            )
        elif self.mode == MODE_B_CHORDS:
            lines = self.lines_gen.generate(
                stream.chord, stream.tempo, stream.melody_notes, stream.beat_position
            )
        elif self.mode == MODE_B_VIBE:
            backing = self.accompaniment.generate(
                stream.chord, stream.tempo, stream.melody_notes, stream.beat_position
            )
            lines = self.lines_gen.generate(
                stream.chord, stream.tempo, stream.melody_notes, stream.beat_position
            )

        duration_16ths = 4.0  # render 1 beat
        audio = self.renderer.render_events_to_audio(
            backing, lines, duration_16ths, stream.tempo
        )
        self._accomp_samples = audio
        self._accomp_index = 0

    def process_callback(self, indata: np.ndarray, outdata: np.ndarray) -> None:
        # Mono: indata shape (block_size,) or (block_size, 1)
        if indata.ndim > 1:
            indata = indata[:, 0]
        block = indata.astype(np.float32).flatten()

        # Accumulate for perception
        self._input_accum = np.concatenate([self._input_accum, block]) if self._input_accum.size else block
        self._blocks_until_perceive -= 1
        if self._blocks_until_perceive <= 0:
            self._blocks_until_perceive = self._perceive_every_n_blocks
            if self._input_accum.size >= 2048:
                stream = self._run_perception(self._input_accum)
                self._generate_and_render(stream)
                self._input_accum = self._input_accum[2048:]

        # Mix: dry guitar + accompaniment
        out_len = outdata.shape[0]
        outdata.fill(0)
        if outdata.ndim == 1:
            outdata[:] = block * self.dry_gain
        else:
            outdata[:, 0] = block * self.dry_gain
            if outdata.shape[1] > 1:
                outdata[:, 1] = block * self.dry_gain

        n_accomp = len(self._accomp_samples) - self._accomp_index
        if n_accomp > 0:
            take = min(out_len, n_accomp)
            acc = self._accomp_samples[self._accomp_index : self._accomp_index + take] * self.wet_gain
            if outdata.ndim == 1:
                outdata[:take] += acc
            else:
                outdata[:take, 0] += acc
                if outdata.shape[1] > 1:
                    outdata[:take, 1] += acc
            self._accomp_index += take

        if outdata.ndim == 1:
            outdata[:] = np.clip(outdata, -1.0, 1.0)
        else:
            outdata[:] = np.clip(outdata, -1.0, 1.0)

    def close(self) -> None:
        self.renderer.close()
