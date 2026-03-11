# How to install JamBuddy

## 1. Get the code

**Already have the project folder?** Use it and go to step 2.

**Fresh clone:**

```powershell
git clone https://github.com/adityaroy10/JamBuddy.git
cd JamBuddy
```

---

## 2. Python environment

You need **Python 3.10 or newer**. Check with:

```powershell
python --version
```

Create and activate a virtual environment:

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```powershell
pip install -r requirements.txt
```

Optional: install the app as a command so you can run `guitar-accompaniment` from anywhere:

```powershell
pip install -e .
```

---

## 4. FluidSynth + SoundFont (required for audio output)

JamBuddy uses FluidSynth to turn MIDI into audio. You need FluidSynth installed and at least one SoundFont (`.sf2`) file.

### Install FluidSynth

- **Windows:** Download from [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases) (e.g. `fluidsynth-2.x.x-win10-x64.zip`), unzip, and add the `bin` folder to your PATH. Or use Chocolatey: `choco install fluidsynth`
- **macOS:** `brew install fluid-synth`
- **Linux:** `sudo apt install fluidsynth` (or your distro’s equivalent)

### Add a SoundFont

FluidSynth does not include sounds; you need a `.sf2` file (e.g. **FluidR3_GM.sf2**). You can find free SoundFonts by searching for “FluidR3_GM.sf2” or “General MIDI soundfont”.

Then either:

- **Option A:** Put the file in the project:
  ```
  JamBuddy/soundfonts/FluidR3_GM.sf2
  ```
- **Option B:** Put it anywhere and set the path in `src/config.py`:
  ```python
  SOUNDFONT_PATH = Path(r"C:\path\to\your\FluidR3_GM.sf2")
  ```

---

## 5. Run the app

From the project folder (with your venv activated):

```powershell
python run.py
```

Or, if you ran `pip install -e .`:

```powershell
guitar-accompaniment
```

Choose a mode, click **Start**, and set your system audio so the guitar input is the default microphone (or your interface) and output goes to your speakers or headphones.

---

## Summary

| Step | Command / action |
|------|-------------------|
| Clone | `git clone https://github.com/adityaroy10/JamBuddy.git` then `cd JamBuddy` |
| Venv | `python -m venv .venv` then activate (see above) |
| Deps | `pip install -r requirements.txt` |
| FluidSynth | Install via link or package manager |
| SoundFont | Place `.sf2` in `soundfonts/` or set `SOUNDFONT_PATH` in `src/config.py` |
| Run | `python run.py` |
