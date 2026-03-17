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
    root.geometry("420x340")
    root.resizable(True, True)

    pipeline: Pipeline = None
    stream: AudioStream = None

    def on_monitor_change(v):
        nonlocal pipeline
        if pipeline is not None:
            pipeline.set_monitor_level(float(v) / 100.0)

    def on_backing_change(v):
        nonlocal pipeline
        if pipeline is not None:
            pipeline.set_backing_level(float(v) / 100.0)

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
        pipeline.set_monitor_level(monitor_var.get() / 100.0)
        pipeline.set_backing_level(backing_var.get() / 100.0)
        
        if use_manual_var.get():
            pipeline.set_manual_chords(manual_chords_var.get())
        try:
            pipeline.renderer.check_backing()
        except (FileNotFoundError, OSError):
            pass  # backing_available stays False; status will show "no backing"
        stream = AudioStream(
            sample_rate=SAMPLE_RATE,
            block_size=BUFFER_SIZE,
            process_callback=pipeline.process_callback,
        )
        stream.start()
        btn_start.config(text="Stop")
        status = f"Running — Mode: {mode_var.get()}"
        if not pipeline.renderer.backing_available:
            status += " (no backing: add FluidSynth bin to PATH)"
        lbl_status.config(text=status)

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

    # Monitor (dry) and Backing (wet) levels
    mix_frame = ttk.Frame(root, padding=(12, 0))
    mix_frame.pack(fill="x", pady=4)
    ttk.Label(mix_frame, text="Monitor (your guitar)", font=("Segoe UI", 9)).pack(anchor="w")
    monitor_var = tk.DoubleVar(value=90.0)
    monitor_scale = ttk.Scale(mix_frame, from_=0, to=100, variable=monitor_var, orient="horizontal", length=200, command=on_monitor_change)
    monitor_scale.pack(anchor="w", pady=(0, 4))
    ttk.Label(mix_frame, text="Backing (accompaniment)", font=("Segoe UI", 9)).pack(anchor="w")
    backing_var = tk.DoubleVar(value=50.0)
    backing_scale = ttk.Scale(mix_frame, from_=0, to=100, variable=backing_var, orient="horizontal", length=200, command=on_backing_change)
    backing_scale.pack(anchor="w", pady=(0, 8))

    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=12, pady=4)
    
    # Manual Chords
    manual_frame = ttk.Frame(root, padding=(12, 0))
    manual_frame.pack(fill="x", pady=4)
    use_manual_var = tk.BooleanVar(value=False)
    chk_manual = ttk.Checkbutton(manual_frame, text="Use Manual Progression", variable=use_manual_var)
    chk_manual.pack(anchor="w")
    manual_chords_var = tk.StringVar(value="C, G, Am, F")
    entry_manual = ttk.Entry(manual_frame, textvariable=manual_chords_var, width=40)
    entry_manual.pack(anchor="w", pady=(2, 0))
    
    ttk.Separator(root, orient="horizontal").pack(fill="x", padx=12, pady=4)

    btn_start = ttk.Button(root, text="Start", command=start_stop)
    btn_start.pack(pady=8)
    lbl_status = ttk.Label(root, text="Choose mode and click Start. Guitar in → audio out.")
    lbl_status.pack(pady=4)

    ttk.Label(root, text="Audio: default input/output. Buffer 512. Set monitor 0% to hear only backing.", font=("Segoe UI", 8), foreground="gray").pack(pady=8)
    root.mainloop()


if __name__ == "__main__":
    main()
