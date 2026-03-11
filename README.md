# JamBuddy — AI Guitar Accompaniment

Audio-in, audio-out AI guitar accompaniment: play solos and get backing + support lines, or play chords and get AI fills, or set chords+vibe and get full backing. 

## Quick start

1. **Create a virtual environment (recommended)**

   ```powershell
   cd d:\USC\Buddy
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. **Install dependencies**

   ```powershell
   pip install -r requirements.txt
   ```

3. **Install FluidSynth (required for audio output)**

   - **Windows**: Install [FluidSynth](https://github.com/FluidSynth/fluidsynth/releases) (e.g. download `fluidsynth-2.x.x-win10-x64.zip` and add the `bin` folder to PATH), or use Chocolatey: `choco install fluidsynth`.
   - **macOS**: `brew install fluid-synth`
   - **Linux**: `sudo apt install fluidsynth` (or your distro package).

4. **Add a SoundFont (.sf2)**

   FluidSynth needs a SoundFont to produce sound. Place a `.sf2` file (e.g. **FluidR3_GM.sf2**) in one of:

   - `d:\USC\Buddy\soundfonts\FluidR3_GM.sf2`
   - Or set `SOUNDFONT_PATH` in `src/config.py` to your `.sf2` path.

   You can find free SoundFonts (e.g. FluidR3_GM.sf2) via a web search.

5. **Run the app**

   ```powershell
   python run.py
   ```

   Or: `python -m app.main`

6. **Choose a mode and click Start**

   - **Solo → Backing + Lines**: Play lead; the app adds chords and support lines.
   - **Chords → Lines**: Play chords; the app adds fills/licks.
   - **Chords + Vibe → Backing**: Same as above with chords/vibe (perception from mic); later you can set progression in UI.

   Connect your guitar (mic or DI) as the default input device and speakers/headphones as output. Audio in → accompaniment mixed with dry guitar → audio out.

### AI chord accompaniment (ReaLchords)

By default the app uses **rule-based** chords (no AI) unless the **realjam** server is running. For **AI chord backing** (ReaLchords):

1. Install realjam: `pip install realjam` (requires Python 3.10–3.12; optional dependency).
2. In a **separate terminal**, start the realjam server: `realjam-start-server` (listens on http://127.0.0.1:8080).
3. Run JamBuddy as usual (`python run.py`). The app will send your melody to the server and use the returned chords for backing. If the server is not running, backing falls back to rule-based chords.

**Lines** (fills/licks) are still rule-based; Magenta or a trained lines model can be added later.

## Project layout

- `src/config.py` — Sample rate, buffer size, backend names (easy to add training later).
- `src/perception` — Audio → symbolic (chords, melody, beat). Implementations: `lightweight` (librosa); training = new backend.
- `src/accompaniment` — Symbolic → backing chords. **AI**: `realjam` (ReaLchords) when the realjam server is running; **fallback**: `rule_based`.
- `src/lines` — Symbolic → fills/support lines. Implementations: `rule_based`; later Magenta/trained.
- `src/render` — MIDI → audio via FluidSynth.
- `src/audio_io` — sounddevice in/out.
- `src/pipeline.py` — Wires perception → accompaniment/lines → render; mode logic.
- `app/main.py` — GUI and entry point.

## Adding training later

- **Perception**: Implement a new class that satisfies `PerceptionInterface` and set `PERCEPTION_BACKEND` in `src/config.py` (and wire in `pipeline.py`).
- **Accompaniment**: Implement `AccompanimentInterface` (e.g. adapter to realjam server or a trained model) and set `ACCOMPANIMENT_BACKEND` in `src/config.py`.
- **Lines**: Implement `LinesInterface` (e.g. Magenta Improv RNN or custom model) and set `LINES_BACKEND` in `src/config.py`.

No training is included in this repo; the design keeps it easy to plug in trained models later.

## Requirements

- Python 3.10+
- FluidSynth installed on the system and a SoundFont (.sf2) file.
