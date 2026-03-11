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
        except (ImportError, FileNotFoundError, OSError):
            # ImportError = no module; FileNotFoundError/OSError = fluidsynth adds C:\tools\fluidsynth\bin and path missing
            return False
        if not self.soundfont_path or not Path(self.soundfont_path).exists():
            return False
        try:
            self._fs = fluidsynth.Synth(samplerate=float(self.sample_rate))
            self._fs.start()
            sfid = self._fs.sfload(str(self.soundfont_path))
            self._fs.program_select(0, sfid, 0, 0)   # channel 0, bank 0, preset 0 (piano)
            self._fs.program_select(1, sfid, 0, 49)   # channel 1: 49 = Slow Strings (smoother than 48)
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
        try:
            if not self._init_synth():
                return np.zeros(int(self.sample_rate * 0.1), dtype=np.float32)  # 100ms silence

            # Convert 16ths to seconds: 1 beat = 4 * 16th, so 16th_dur_sec = 60/(tempo*4)
            sixteenth_sec = 60.0 / (tempo * 4.0)
            total_sec = duration_16ths * sixteenth_sec
            n_samples = int(total_sec * self.sample_rate)
            if n_samples <= 0:
                n_samples = int(0.1 * self.sample_rate)

            # FluidSynth doesn't give us a simple "render N seconds" API easily; we generate in small chunks
            chunk_16ths = 1.0
            chunk_sec = chunk_16ths * sixteenth_sec
            out = np.zeros(n_samples, dtype=np.float32)

            # Backing: play as block chord (all notes on together) so it sounds full, not arpeggio
            if backing_events:
                chord_dur_16ths = max(dur for _, _, dur in backing_events) if backing_events else 2.0
                chord_sec = chord_dur_16ths * sixteenth_sec
                for note, vel, dur in backing_events:
                    self._fs.noteon(1, note, vel)
                ns = int(chord_sec * self.sample_rate)
                if ns > 0:
                    buf = self._fs.get_samples(ns)
                    if buf is not None and len(buf) > 0:
                        if hasattr(buf, 'dtype'):
                            buf = buf.astype(np.float32) / 32768.0
                        else:
                            buf = np.frombuffer(buf, dtype=np.int16).astype(np.float32) / 32768.0
                        if len(buf) >= 2:
                            buf = (buf[::2] + buf[1::2]) / 2  # stereo to mono
                        end_idx = min(len(buf), n_samples)
                        out[:end_idx] += buf[:end_idx]
                for note, vel, dur in backing_events:
                    self._fs.noteoff(1, note)

            t_16th = chord_dur_16ths if backing_events else 0.0

            # Lines: render each note (melody/fills)
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

            out = np.clip(out, -1.0, 1.0)
            return out
        except OSError:
            # FluidSynth DLL/path not found (e.g. C:\tools\fluidsynth\bin) or similar
            self._ready = False
            if self._fs is not None:
                try:
                    self._fs.delete()
                except Exception:
                    pass
                self._fs = None
            return np.zeros(int(self.sample_rate * 0.1), dtype=np.float32)
        except Exception:
            return np.zeros(int(self.sample_rate * 0.1), dtype=np.float32)

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

    @property
    def backing_available(self) -> bool:
        return self._ready

    def check_backing(self) -> bool:
        return self._init_synth()
