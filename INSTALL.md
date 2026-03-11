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

You need **Python 3.10, 3.11, or 3.12**. (Python 3.14 is too new — most scientific packages don’t have pre-built wheels yet, so `pip install` will try to build from source and fail.)

Check your version:

```powershell
python --version
```

If you see 3.14 or higher, install Python 3.12 from [python.org](https://www.python.org/downloads/) (or use [pyenv](https://github.com/pyenv/pyenv-win) / [conda](https://docs.conda.io/) and create an environment with 3.12).

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

**Note:** If you run the `fluidsynth` command in a terminal you may see errors about `C:\ProgramData\soundfonts\default.sf2` or "MIDI in devices". That is the **standalone** FluidSynth CLI; JamBuddy uses the SoundFont in `soundfonts/FluidR3_GM.sf2` and drives the synth from the app (no MIDI input needed). You can ignore those messages when running `python run.py`.

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

## 6. (Optional) AI chord accompaniment (ReaLchords)

By default, chord backing is **rule-based**. For **AI chord backing** (ReaLchords):

**If `pip install realjam` fails with "onnxruntime ... no matching distributions" or "ResolutionImpossible":** your venv is **Python 3.14** (pip may show `cp314` in the error). realjam needs **Python 3.10, 3.11, or 3.12** because `onnxruntime` has no wheel for 3.14. You must recreate the venv with 3.12:

1. **Install Python 3.12** if needed: [python.org/downloads](https://www.python.org/downloads/) — get 3.12.x (not 3.14).
2. **Recreate the venv** from the project root:
   ```powershell
   cd D:\USC\Buddy
   Remove-Item -Recurse -Force .venv
   py -3.12 -m venv .venv
   ```
   If `py -3.12` is not found, use the full path to Python 3.12, e.g. `C:\Python312\python.exe -m venv .venv`.
3. **Activate and install**:
   ```powershell
   .venv\Scripts\activate
   python --version   # must show 3.12.x
   pip install -r requirements.txt
   pip install realjam
   ```
4. In **another terminal** (same venv activated), start the realjam server:
   ```powershell
   realjam-start-server
   ```
5. Run JamBuddy as usual. With the server running, the app uses ReaLchords for backing; otherwise it falls back to rule-based chords.

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
