# MIDI Cleaner

Web application for cleaning multi-track MIDI files produced by AI transcription tools (Suno, etc.).

Upload a MIDI file exported from Guitar Pro or similar DAW, configure cleaning parameters, preview the result with notation and playback, then download the cleaned version ready for manual editing.

## Features

- **Voice Merging** — consolidate voices 2/3/4 into voice 1 per track, align chord durations for single-voice output in Guitar Pro
- **Overlap Resolution** — merge overlapping same-pitch notes (earliest onset, latest offset, highest velocity)
- **Triplet Removal** — detect triplet durations and convert them to straight eighth notes
- **Quantization** — snap note timing to a rhythmic grid (quarter / eighth / sixteenth), bar-aware clipping to prevent notes crossing bar boundaries
- **CC Filtering** — strip MIDI Control Change messages (sustain CC#64, legato CC#68, or custom)
- **Noise Filter** — remove parasitic short/quiet notes with configurable thresholds per track
- **VexFlow Notation** — sheet music preview for each track with treble/bass clef and Guitar TAB
- **Tone.js Playback** — play individual tracks or the full MIDI in the browser with transport controls (play, pause, stop, rewind, seek)
- **Comparison** — switch between original and processed versions for notation and playback
- **Russian / English UI** — language toggle in the top-right corner
- **Tolerant Parsing** — handles invalid MIDI meta events (e.g. corrupt key signatures from AI tools) gracefully

## Processing Parameters

### Global Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Merge Voices** | toggle | on | Consolidate all MIDI channels within each track to the primary channel. Aligns chord durations so Guitar Pro keeps everything in Voice 1. |
| **Remove Overlaps** | toggle | on | When two notes of the same pitch overlap on the same channel, merge them into a single note spanning the full duration. |
| **Remove Triplets** | toggle | on | Detect notes with triplet durations and convert them to straight eighth notes. |
| **Triplet Tolerance** | 0.05–0.30 | 0.15 | Sensitivity for triplet detection. Lower = stricter matching, higher = catches more borderline cases. |
| **Quantize** | toggle | on | Snap note onset times and durations to the nearest grid position. |
| **Grid Resolution** | select | Eighth | Quantization grid size: Quarter note, Eighth note, or Sixteenth note. |
| **Remove CC Messages** | toggle | on | Strip selected MIDI Control Change messages from all tracks. |
| **CC Numbers to Remove** | checkboxes | CC#64, CC#68 | CC#64 = Sustain Pedal, CC#68 = Legato Footswitch. |
| **Noise Filter** | toggle | on | Remove short and quiet parasitic notes. |
| **Min Note Duration** | 0–480 ticks | 120 | Notes shorter than this (in MIDI ticks) are removed. At 480 PPQ: 120 ticks = sixteenth note. |
| **Min Velocity** | 0–127 | 20 | Notes with MIDI velocity below this are removed. |
| **Start Processing from Bar** | 1–999 | 1 | Skip already-cleaned bars. Set to 1 to process everything, or higher to preserve manually cleaned sections at the beginning. |

### Per-Track Overrides

Each track card has its own **Min Duration** and **Min Velocity** sliders that override the global noise filter settings for that specific track. Tracks can also be individually disabled via checkboxes.

### Processing Pipeline Order

1. **Voice Merger** — merge channels, resolve same-pitch overlaps, align chord durations
2. **CC Filter** — remove sustain/legato CC messages
3. **Triplet Remover** — convert triplet durations to straight eighths
4. **Quantizer** — snap to grid, clip at bar boundaries
5. **Noise Filter** — remove short/quiet notes
6. **Final Chord Alignment** — ensure simultaneous notes have identical durations (prevents Guitar Pro multi-voice artifacts)
7. **Meta Cleanup** — strip stray tempo/time-signature events from data tracks (Type 1 MIDI: these belong only in the conductor track)

## Requirements

- Python 3.10+
- Flask 3.0+
- mido 1.3+

External (loaded from CDN in the browser):
- [VexFlow 4.2.5](https://www.vexflow.com/) — music notation rendering
- [Tone.js 14.7](https://tonejs.github.io/) — Web Audio playback

## Running Locally

```bash
# Install dependencies and start dev server
make dev

# Or with Podman
make run
```

The app will be available at `http://localhost:5000`.

## Deployment

### Deploy to remote server (Podman + systemd)

```bash
make deploy
```

This will:
1. Sync the project to the remote server via rsync
2. Build the Podman container image
3. Start the container on port 8040 with `--restart=always`
4. Open port 8040 in firewalld
5. Generate and enable a systemd service for auto-start on reboot

Configuration variables in `Makefile`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEPLOY_HOST` | `alma` | SSH hostname of the target server |
| `DEPLOY_USER` | `mgrigorov` | SSH user |
| `DEPLOY_DIR` | `/home/mgrigorov/midi-cleaner` | Remote directory |
| `REMOTE_PORT` | `8040` | Port to expose on the server |

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make build` | Build the Podman image locally |
| `make run` | Build and run locally on port 5000 |
| `make stop` | Stop and remove local container |
| `make restart` | Stop then run |
| `make logs` | Tail container logs |
| `make clean` | Stop container and remove image |
| `make dev` | Install deps and run Flask dev server directly |
| `make deploy` | Full deploy to remote server |

## Project Structure

```
.
├── app.py                  # Flask application and API routes
├── config.py               # Default configuration and constants
├── Dockerfile
├── Makefile
├── requirements.txt
├── processors/
│   ├── pipeline.py         # Processing orchestrator
│   ├── voice_merger.py     # Channel merging + chord alignment
│   ├── cc_filter.py        # Control Change message removal
│   ├── triplet_remover.py  # Triplet detection and conversion
│   ├── quantizer.py        # Bar-aware grid quantization
│   └── noise_filter.py     # Short/quiet note removal
├── utils/
│   ├── midi_helpers.py     # MIDI utility functions
│   ├── midi_analyzer.py    # Notation and playback data generation
│   └── track_detector.py   # Instrument type detection
├── templates/
│   └── index.html          # Single-page frontend
└── static/
    ├── css/style.css
    └── js/app.js           # Frontend logic (upload, playback, notation, i18n)
```
