"""
Main entry point: GUI with mode selection, audio in/out.
Run: python -m app.main  or  python run.py
"""
import sys
import threading
from pathlib import Path

# Add project root to path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.config import SAMPLE_RATE, BUFFER_SIZE, get_soundfont_path
from src.audio_io import AudioStream
from src.pipeline import Pipeline, MODE_A_SOLO, MODE_B_CHORDS, MODE_B_VIBE


def main():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("JamBuddy — AI Guitar Accompaniment")
    root.geometry("420x280")
    root.resizable(True, True)

    pipeline: Pipeline = None
    stream: AudioStream = None

    def on_mode_change():
        nonlocal pipeline
        mode = mode_var.get()
        if pipeline:
            pipeline.set_mode(mode)
        lbl_status.config(text=f"Mode: {mode}")

    def start_stop():
        nonlocal pipeline, stream
        if stream and stream.is_running:
            stream.stop()
            if pipeline:
                pipeline.close()
            btn_start.config(text="Start")
            lbl_status.config(text="Stopped")
            return
        sf = get_soundfont_path()
        if not sf:
            lbl_status.config(text="No SoundFont found. Install FluidSynth and add a .sf2 file.")
            return
        pipeline = Pipeline(sample_rate=SAMPLE_RATE, block_size=BUFFER_SIZE, mode=mode_var.get())
        stream = AudioStream(
            sample_rate=SAMPLE_RATE,
            block_size=BUFFER_SIZE,
            process_callback=pipeline.process_callback,
        )
        stream.start()
        btn_start.config(text="Stop")
        lbl_status.config(text=f"Running — Mode: {mode_var.get()}")

    # Mode selection (both A and B)
    ttk.Label(root, text="Mode", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
    mode_var = tk.StringVar(value=MODE_A_SOLO)
    modes = [
        (MODE_A_SOLO, "Solo → Backing + Lines (you play lead, AI adds chords and support lines)"),
        (MODE_B_CHORDS, "Chords → Lines (you play chords, AI adds fills/licks)"),
        (MODE_B_VIBE, "Chords + Vibe → Backing (you set chords/vibe, AI plays backing + lines)"),
    ]
    for val, label in modes:
        rb = ttk.Radiobutton(root, text=label, variable=mode_var, value=val, command=on_mode_change)
        rb.pack(anchor="w", padx=24, pady=2)
    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=12, pady=8)

    btn_start = ttk.Button(root, text="Start", command=start_stop)
    btn_start.pack(pady=8)
    lbl_status = ttk.Label(root, text="Choose mode and click Start. Guitar in → audio out.")
    lbl_status.pack(pady=4)

    ttk.Label(root, text="Audio: default input/output devices. Buffer size 256.", font=("Segoe UI", 8), foreground="gray").pack(pady=8)
    root.mainloop()


if __name__ == "__main__":
    main()
