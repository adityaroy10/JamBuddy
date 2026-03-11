"""
Configuration for AI Guitar Accompaniment.
Central place for buffer sizes, sample rate, and backend selection.
Training can be added later by switching backends here or via env/config file.
"""
from pathlib import Path
from typing import Optional

# Audio (Option A: 256 samples for latency vs robustness)
SAMPLE_RATE = 44100
BUFFER_SIZE = 256  # reduce to 128 if no dropouts
INPUT_DEVICE: Optional[int] = None  # None = default
OUTPUT_DEVICE: Optional[int] = None  # None = default

# Backends (easy to swap for training later)
ACCOMPANIMENT_BACKEND = "rule_based"  # "rule_based" | "realjam"
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
