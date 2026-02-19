# MIDI Cleaner

Web application for cleaning multi-track MIDI files produced by AI transcription tools (Suno, etc.).

Upload a MIDI file exported from Guitar Pro or similar DAW, configure cleaning parameters, preview the result with notation and playback, then download the cleaned version ready for manual editing.

## Features

- **Tempo Deduplication** — remove redundant `set_tempo` meta events that cause notation software to show ♩=91 on every bar; real tempo changes are preserved
- **Pitch Cluster Removal** — collapse tight bundles of near-pitch notes that start almost simultaneously (AI transcription artefact on FX/distortion tracks) into a single representative note
- **Voice Merging** — consolidate voices 2/3/4 into voice 1 per track, align chord durations for single-voice output in Guitar Pro
- **Overlap Resolution** — merge overlapping same-pitch notes (earliest onset, latest offset, highest velocity)
- **Same-Pitch Overlap Resolver** — remove duplicate overlapping notes of the same pitch per (channel, pitch); keeps the longer/louder note, removes the weaker duplicate entirely (no trimming)
- **Triplet Removal** — detect triplet durations and convert them to straight eighth notes
- **Quantization** — snap note timing to a rhythmic grid (quarter / eighth / sixteenth), bar-aware clipping to prevent notes crossing bar boundaries
- **CC Filtering** — strip MIDI Control Change messages (sustain CC#64, legato CC#68, or custom)
- **Noise Filter** — remove parasitic short/quiet notes with configurable thresholds per track
- **Track Flattener** — optionally merge all tracks into a single MTrk (Type 0) for easier manual cleanup in a notation editor
- **VexFlow Notation** — sheet music preview for each track with treble/bass clef and Guitar TAB
- **Tone.js Playback** — play individual tracks or the full MIDI in the browser with transport controls (play, pause, stop, rewind, seek)
- **Comparison** — switch between original and processed versions for notation and playback
- **Russian / English UI** — language toggle in the top-right corner
- **Auto Optimize** — Optuna-based parameter search that automatically finds the best cleaning settings for a given MIDI file; detects track type and adjusts search ranges accordingly
- **Tolerant Parsing** — handles invalid MIDI meta events (e.g. corrupt key signatures from AI tools) gracefully

## Processing Parameters

### Global Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Tempo Dedup: Enabled** | toggle | on | Remove duplicate `set_tempo` events. Keeps the first occurrence and any real tempo changes, strips identical repeats. |
| **Pitch Cluster: Enabled** | toggle | on | Enable pitch-cluster denoising. When on, near-pitch notes that start within the onset window are merged into one note. |
| **Pitch Cluster: Time Window** | ticks | 20 | Maximum onset spread (in MIDI ticks) for notes to be considered simultaneous. |
| **Pitch Cluster: Pitch Threshold** | semitones | 1 | Maximum semitone distance between notes in the same cluster. |
| **Same-Pitch Overlap Resolver: Enabled** | toggle | on | Remove duplicate overlapping notes of the same pitch within each (channel, pitch). Keeps the longer note; tie-break by velocity then onset. |
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
| **Merge Tracks: Enabled** | toggle | off | Flatten all tracks into a single MTrk (Type 0 MIDI). Useful for manual cleanup in a notation editor. |
| **Merge Tracks: Include CC** | toggle | off | Include CC events in the merged output. When off, all CC messages are stripped during merge. |
| **Merge Tracks: CC Whitelist** | list | 64, 68 | When Include CC is on, only these CC numbers are kept. Empty list = keep all CC. |

### Auto Optimize

The Auto Optimize panel (visible after uploading a MIDI file) uses [Optuna](https://optuna.org/) to search for the best combination of cleaning parameters. It automatically detects the dominant track type (guitar, vocal, bass, etc.) and adjusts the search ranges accordingly.

**Search space:**

| Parameter | Range |
|-----------|-------|
| min_duration | 40–240 (adjusted by track type) |
| min_velocity | 0–40 (adjusted by track type) |
| cluster_window | 10–120 (adjusted by track type) |
| cluster_pitch | 0–2 |
| triplet_tolerance | 0.05–0.30 |
| quantize | true / false |
| remove_triplets | true / false |
| merge_voices | true / false |

**Scoring function:**

```
score = unique_pitches * 2 + avg_duration - short_note_ratio * 5 - overlap_count * 3 - voice_count * 4
```

**Early stopping:** optimization stops when improvement is < 0.5% for 4 consecutive iterations, or score declines > 1% for 2 consecutive iterations, or after the configured maximum trials (default 40).

**API:** `POST /api/optimize` starts the optimization in a background thread; `GET /api/optimize/status` returns live progress (current trial, best score, parameters); `POST /api/optimize/apply` applies the best result as the processed file.

### Per-Track Overrides

Each track card has its own **Min Duration** and **Min Velocity** sliders that override the global noise filter settings for that specific track. Tracks can also be individually disabled via checkboxes.

### Processing Pipeline Order

0. **Tempo Deduplicator** — remove redundant `set_tempo` meta events (runs on all tracks including conductor)
1. **Pitch Cluster Processor** — collapse near-pitch simultaneous note bundles to a single note
2. **Voice Merger** — merge channels, resolve same-pitch overlaps, align chord durations
3. **CC Filter** — remove sustain/legato CC messages
4. **Triplet Remover** — convert triplet durations to straight eighths
5. **Quantizer** — snap to grid, clip at bar boundaries
6. **Noise Filter** — remove short/quiet notes
7. **Same-Pitch Overlap Resolver** — deduplicate overlapping notes of the same pitch per (channel, pitch)
8. **Final Chord Alignment** — ensure simultaneous notes have identical durations (prevents Guitar Pro multi-voice artifacts)
9. **Meta Cleanup** — strip stray tempo/time-signature events from data tracks (Type 1 MIDI: these belong only in the conductor track)
10. **Merge Tracks** *(file-level, optional)* — flatten all tracks into a single MTrk (Type 0) for manual cleanup

## Requirements

- Python 3.10+
- Flask 3.0+
- mido 1.3+
- optuna 3.5+

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

## Running Tests

```bash
# Run all tests (including E2E and optimizer tests)
python -m pytest tests/ -v

# Run only the end-to-end test
python -m pytest tests/test_e2e_process.py -v

# Run only the auto-tuner tests
python -m pytest tests/test_auto_tuner.py -v
```

The E2E test uploads the test asset MIDI (`tests/assets/The Dragon and The Princess (FX).mid`),
processes it with recommended settings, and saves the result to:

```
tests/output/The Dragon and The Princess (FX)_processed_by_tests.mid
```

The auto-tuner test runs Optuna optimization on the same MIDI and saves the best result to:

```
tests/output/optimized.mid
```

No external services or GUI required — all tests use Flask's built-in test client.

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
│   ├── pipeline.py                    # Processing orchestrator
│   ├── tempo_deduplicator.py          # Redundant set_tempo removal
│   ├── pitch_cluster.py              # Near-pitch simultaneous note clustering
│   ├── voice_merger.py               # Channel merging + chord alignment
│   ├── cc_filter.py                  # Control Change message removal
│   ├── triplet_remover.py            # Triplet detection and conversion
│   ├── quantizer.py                  # Bar-aware grid quantization
│   ├── noise_filter.py               # Short/quiet note removal
│   ├── same_pitch_overlap_resolver.py # Same-pitch overlap deduplication
│   └── merge_tracks_to_single.py     # Multi-track → single-track flattener
├── optimizers/
│   └── auto_tuner.py       # Optuna-based parameter optimization
├── utils/
│   ├── midi_helpers.py     # MIDI utility functions
│   ├── midi_analyzer.py    # Notation and playback data generation
│   └── track_detector.py   # Instrument type detection
├── templates/
│   └── index.html          # Single-page frontend
├── static/
│   ├── css/style.css
│   └── js/app.js           # Frontend logic (upload, playback, notation, i18n)
└── tests/
    ├── assets/              # Test MIDI files
    ├── output/              # Processed MIDI artifacts (git-ignored)
    ├── test_e2e_process.py  # End-to-end upload/process/download test
    └── ...                  # Unit tests for individual processors
```
