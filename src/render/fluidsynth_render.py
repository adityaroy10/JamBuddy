"""
Render MIDI events to audio using FluidSynth.
Requires FluidSynth to be installed on the system (e.g. choco install fluidsynth on Windows).
"""
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

# (midi_note, velocity, duration_16ths)
MIDIEvent = Tuple[int, int, float]


class FluidSynthRender:
    """Real-time MIDI -> float audio. Uses pyfluidsynth."""

    def __init__(self, sample_rate: int = 44100, soundfont_path: Optional[Path] = None):
        self.sample_rate = sample_rate
        self.soundfont_path = soundfont_path
        self._fs = None
        self._synth_id = 0
        self._ready = False

    def _init_synth(self) -> bool:
        if self._ready:
            return True
        try:
            import fluidsynth
        except ImportError:
            return False
        if not self.soundfont_path or not Path(self.soundfont_path).exists():
            return False
        try:
            self._fs = fluidsynth.Synth(samplerate=float(self.sample_rate))
            self._fs.start()
            sfid = self._fs.sfload(str(self.soundfont_path))
            self._fs.program_select(0, sfid, 0, 0)   # channel 0, bank 0, preset 0 (usually piano)
            self._fs.program_select(1, sfid, 0, 48)   # channel 1, e.g. strings or pad for backing
            self._ready = True
            return True
        except Exception:
            return False

    def render_events_to_audio(
        self,
        backing_events: List[MIDIEvent],
        lines_events: List[MIDIEvent],
        duration_16ths: float,
        tempo: float,
    ) -> np.ndarray:
        """Render backing + lines events to a float32 mono array. duration_16ths = length in 16th notes."""
        if not self._init_synth():
            return np.zeros(int(self.sample_rate * 0.1), dtype=np.float32)  # 100ms silence

        # Convert 16ths to seconds: 1 beat = 4 * 16th, so 16th_dur_sec = 60/(tempo*4)
        sixteenth_sec = 60.0 / (tempo * 4.0)
        total_sec = duration_16ths * sixteenth_sec
        n_samples = int(total_sec * self.sample_rate)
        if n_samples <= 0:
            n_samples = int(0.1 * self.sample_rate)

        # FluidSynth doesn't give us a simple "render N seconds" API easily; we generate in small chunks
        # For simplicity: render one chunk per 16th note and concatenate
        chunk_16ths = 1.0
        chunk_sec = chunk_16ths * sixteenth_sec
        chunk_samples = int(chunk_sec * self.sample_rate)
        out = np.zeros(n_samples, dtype=np.float32)

        t_16th = 0.0
        for note, vel, dur in backing_events:
            start_s = t_16th * sixteenth_sec
            end_s = (t_16th + dur) * sixteenth_sec
            self._fs.noteon(1, note, vel)  # channel 1 = backing
            ns = int((end_s - start_s) * self.sample_rate)
            if ns > 0:
                buf = self._fs.get_samples(ns)  # ns = stereo frames, returns 2*ns int16
                if buf is not None and len(buf) > 0:
                    if hasattr(buf, 'dtype'):
                        buf = buf.astype(np.float32) / 32768.0
                    else:
                        buf = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
                    if len(buf) >= 2:
                        buf = (buf[::2] + buf[1::2]) / 2  # stereo to mono
                    start_idx = int(start_s * self.sample_rate)
                    end_idx = min(start_idx + len(buf), n_samples)
                    if start_idx < len(out) and end_idx > start_idx:
                        out[start_idx:end_idx] += buf[: end_idx - start_idx]
            self._fs.noteoff(1, note)
            t_16th += max(dur, 0.25)

        for note, vel, dur in lines_events:
            start_s = 0.0  # simple: start at 0 for lines in this chunk
            end_s = dur * sixteenth_sec
            self._fs.noteon(0, note, vel)  # channel 0 = lines
            ns = int(end_s * self.sample_rate)
            if ns > 0:
                buf = self._fs.get_samples(ns)
                if buf is not None and len(buf) > 0:
                    if hasattr(buf, 'dtype'):
                        buf = buf.astype(np.float32) / 32768.0
                    else:
                        buf = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
                    if len(buf) >= 2:
                        buf = (buf[::2] + buf[1::2]) / 2
                    end_idx = min(len(buf), n_samples)
                    out[:end_idx] += buf[:end_idx] * 0.7  # mix lines slightly lower
            self._fs.noteoff(0, note)

        # Clip to avoid overflow
        out = np.clip(out, -1.0, 1.0)
        return out

    def get_silence(self, num_samples: int) -> np.ndarray:
        return np.zeros(num_samples, dtype=np.float32)

    def close(self) -> None:
        if self._fs is not None:
            try:
                self._fs.delete()
            except Exception:
                pass
            self._fs = None
        self._ready = False
