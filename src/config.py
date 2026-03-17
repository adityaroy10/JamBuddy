"""
Configuration for AI Guitar Accompaniment.
Central place for buffer sizes, sample rate, and backend selection.
Training can be added later by switching backends here or via env/config file.
"""
from pathlib import Path
from typing import Optional

# Audio (Option A: 256 samples for latency vs robustness)
SAMPLE_RATE = 44100
BUFFER_SIZE = 512  # 256 was causing underflows when perception+render run in callback; 512 gives more headroom
INPUT_DEVICE: Optional[int] = None  # None = default
OUTPUT_DEVICE: Optional[int] = None  # None = default

# Input gate: below this RMS (0.0–1.0) we treat as silence — no backing, no dry (reduces notes-on-silence and hiss)
INPUT_GATE_THRESHOLD = 0.01  # raise if backing still triggers on silence; lower if quiet playing is cut off

# Backends (easy to swap for training later)
# Use "realjam" for AI chords (ReaLchords); run realjam-start-server in another terminal. Falls back to rule-based if server unavailable.
ACCOMPANIMENT_BACKEND = "markov"  # "rule_based" | "realjam" | "markov"
LINES_BACKEND = "rule_based"         # "rule_based" | "magenta"
PERCEPTION_BACKEND = "lightweight"   # "lightweight" | "trained"

# FluidSynth: user must have FluidSynth installed and a .sf2 file
# On Windows: choco install fluidsynth, or download from GitHub releases
SOUNDFONT_PATH: Optional[Path] = None  # Set to Path("path/to/FluidR3_GM.sf2") or leave None to try common paths

def get_soundfont_path() -> Optional[Path]:
    if SOUNDFONT_PATH and SOUNDFONT_PATH.exists():
        return SOUNDFONT_PATH
    root = Path(__file__).resolve().parent.parent  # project root
    candidates = [
        root / "soundfonts" / "FluidR3_GM.sf2",
        Path(__file__).parent / "soundfonts" / "FluidR3_GM.sf2",
        Path.home() / ".local" / "share" / "soundfonts" / "FluidR3_GM.sf2",
        Path("C:/Program Files/FluidSynth/soundfonts/FluidR3_GM.sf2"),
        Path("C:/soundfonts/FluidR3_GM.sf2"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None
