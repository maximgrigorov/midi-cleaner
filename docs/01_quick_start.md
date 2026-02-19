# Quick Start

## What This Tool Does

MIDI Cleaner takes AI-generated MIDI files and removes the digital noise that makes them hard to work with in notation software. Think of it like cleaning up a rough recording — keeping the music but removing the artifacts.

## Getting Started

1. **Open the app** in your browser (usually `http://localhost:5000`)
2. **Drop your MIDI file** onto the upload area, or click to browse
3. **Choose a preset** from the dropdown at the top of the settings panel:
   - "Auto (Recommended)" will detect your track type and pick sensible defaults
   - Or pick one manually: "FX / Preserve", "Strings / Cleaner", etc.
4. **Click "Process & Clean"**
5. **Check the Processing Log** (collapsible panel) to see what changed
6. **Download** your cleaned MIDI file

That's it for the basic workflow. For better results, read on.

## The Processing Log

After every processing run, a "Processing Log" panel appears showing:
- **Total time** — how long processing took
- **Notes in / out** — how many notes went in and came out
- **Step-by-step breakdown** — each cleaning step, what it did, and how many notes it affected

You can also download this data as `report.json` for your records.

## Using Auto-Tune

If you want the tool to find optimal settings automatically:

1. Upload your MIDI file
2. Switch to the **"Auto-Tune"** tab
3. Set the number of trials (30–40 is usually enough)
4. Optionally enable **LLM Guidance** for AI-assisted parameter suggestions
5. Click **"Start Optimization"**
6. Wait for it to finish (it tests many parameter combinations)
7. Click **"Apply Best Parameters"** — this updates all settings to the optimal values and switches to Manual mode so you can review them
8. Click **"Process & Clean"** to generate the output with those settings
9. **Download** the result

## Tips

- **Start with a preset** rather than tweaking every slider
- **Use "FX / Preserve"** for most AI-transcribed stems — it's the safest default
- **Check the log** — if you see lots of notes removed, you might want gentler settings
- **Save your report** — if you find settings that work well, the report records them exactly
