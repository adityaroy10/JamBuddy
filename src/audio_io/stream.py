"""
Audio I/O: guitar in, mixed accompaniment out.
Uses sounddevice with configurable buffer size for low latency.
"""
import queue
import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional

from src.config import SAMPLE_RATE, BUFFER_SIZE, INPUT_DEVICE, OUTPUT_DEVICE


def _default_process_callback(
    input_audio: np.ndarray,
    output_audio: np.ndarray,
    dry_gain: float = 0.9,
    wet_gain: float = 0.5,
) -> None:
    """Default: pass through input (dry) and copy accompaniment into output. Caller replaces this."""
    # Stereo: assume input is (N,) or (N,2); output same shape
    if input_audio.ndim == 1:
        out_len = min(len(input_audio), len(output_audio))
        output_audio[:out_len] = input_audio[:out_len] * dry_gain
    else:
        out_len = min(input_audio.shape[0], output_audio.shape[0])
        output_audio[:out_len] = input_audio[:out_len] * dry_gain


class AudioStream:
    """Full-duplex stream: read input, call processor, write output."""

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        block_size: int = BUFFER_SIZE,
        input_device: Optional[int] = None,
        output_device: Optional[int] = None,
        process_callback: Optional[Callable[[np.ndarray, np.ndarray], None]] = None,
    ):
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.input_device = input_device if input_device is not None else INPUT_DEVICE
        self.output_device = output_device if output_device is not None else OUTPUT_DEVICE
        self._process = process_callback or _default_process_callback
        self._stream: Optional[sd.Stream] = None
        self._accomp_queue: queue.Queue = queue.Queue()
        self._running = False

    def set_process_callback(self, cb: Callable[[np.ndarray, np.ndarray], None]) -> None:
        self._process = cb

    def _audio_callback(self, indata: np.ndarray, outdata: np.ndarray, frames: int, time_info, status):
        if status:
            print("Audio status:", status)
        try:
            self._process(indata.copy(), outdata)
        except Exception as e:
            print("Process error:", e)
            outdata.fill(0)

    def start(self) -> None:
        if self._stream is not None:
            return
        # sounddevice.Stream uses "device" (single or pair), not input_device/output_device
        stream_kw = dict(
            samplerate=self.sample_rate,
            blocksize=self.block_size,
            dtype=np.float32,
            channels=1,
            callback=self._audio_callback,
        )
        if self.input_device is not None or self.output_device is not None:
            stream_kw["device"] = (self.input_device, self.output_device)
        self._stream = sd.Stream(**stream_kw)
        self._stream.start()
        self._running = True

    def stop(self) -> None:
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    @property
    def is_running(self) -> bool:
        return self._running and self._stream is not None and self._stream.active
