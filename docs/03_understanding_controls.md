# Understanding Controls

This page explains what each setting does in plain language.

---

## Presets

**What it does:** A preset is a pre-configured combination of settings optimized for a specific instrument and goal.

**When to use it:** Always start with a preset. "Auto (Recommended)" detects your track type and picks the best starting point.

**Advanced toggle:** By default, rarely-used controls are hidden. Check "Show Advanced" to see everything.

---

## Deduplicate Tempo

**What it does:** AI transcription tools sometimes write the tempo marking (like "120 BPM") hundreds of times throughout the file. Notation software reads each one and clutters the score with tempo markings.

**Recommendation:** Always ON. There is almost no reason to keep duplicate tempo events.

---

## Merge Voices

**What it does:** In notation software, a "voice" is a separate musical line within the same staff. AI transcription often creates 2–4 voices when one would suffice, making the score confusing.

This control consolidates notes onto a single channel and aligns chord durations, reducing unnecessary voice splits.

**Recommendation:** ON for melody, bass, and FX tracks. OFF for strings or piano where multiple voices are intentional.

---

## Remove Overlaps

**What it does:** Resolves notes that start before the previous one ends. Overlapping notes on the same pitch force notation software to create separate voices.

**Recommendation:** Almost always ON.

---

## Remove Triplets

**What it does:** AI transcription sometimes creates notes with triplet-like durations (three notes in the time of two) when the original music had straight rhythms. This converts those back to regular eighth or quarter notes.

**Recommendation:** OFF for jazz or swing music. ON for rock, pop, and electronic music.

---

## Triplet Tolerance

**What it does:** Controls how aggressively the tool detects triplets. Lower values (0.05) only catch notes that are very close to triplet timing. Higher values (0.25) catch more, but might incorrectly convert some notes.

**Recommendation:** Start at 0.15 (default).

---

## Quantize

**What it does:** Snaps note timing to a rhythmic grid (quarter notes, eighth notes, or sixteenth notes). Makes the score look cleaner but may remove intentional timing nuances.

**Recommendation:** OFF for expressive music (rubato, FX). ON for tightly rhythmic music.

---

## Grid Resolution

**What it does:** Sets the size of the quantization grid.
- **Quarter note:** Very coarse — only useful for slow, sustained parts
- **Eighth note:** Good default — works for most music
- **Sixteenth note:** Fine grid — preserves more timing detail

---

## Remove CC Messages

**What it does:** Strips "Control Change" MIDI messages. These are non-note data like sustain pedal (CC#64) and legato (CC#68). They can clutter the MIDI file without adding anything useful for notation.

**Recommendation:** ON for notation cleanup. OFF if you plan to use the MIDI for playback with realistic instruments.

---

## Pitch Cluster

**What it does:** When AI transcription generates a note at, say, C4 and another at C#4 at nearly the same time, it's almost certainly noise. This merges notes that are close in both pitch and time into the strongest one.

- **Time Window:** How close in time (in ticks) two notes must be to be considered "simultaneous." Default 20.
- **Pitch Threshold:** How many semitones apart two notes can be and still get merged. 0 = only same pitch. 1 = next semitone. 2 = two semitones.

**Recommendation:** ON with threshold 1 for most tracks. Set to 0 for vocals.

---

## Noise Filter

**What it does:** Removes notes that are too short or too quiet to be real. These are the digital equivalent of background noise.

- **Min Note Duration:** Notes shorter than this (in ticks) are removed. 480 ticks = 1 quarter note at standard resolution.
- **Min Velocity:** Notes quieter than this (0–127 scale) are removed.

**Recommendation:** Start with 120 ticks / velocity 20. Adjust based on the processing log.

---

## Same-Pitch Overlap Resolver

**What it does:** When two notes of the exact same pitch overlap in time, one is almost always a transcription artifact. This removes the less important one based on: longer duration wins, then higher velocity, then earlier timing.

**Recommendation:** Almost always ON.

---

## Start Processing from Bar

**What it does:** Skips the first N bars. Useful if you've already cleaned part of the file and only want to process the rest.

---

## Merge All Tracks

**What it does:** Combines all tracks into a single track (Type 0 MIDI). Useful for simple editing but loses track separation.

**Recommendation:** OFF unless you specifically need a single-track file.

---

## Auto Optimize

**What it does:** Automatically tries many parameter combinations and picks the one that produces the cleanest result. Uses a scoring system that rewards clarity while penalizing over-cleaning.

**LLM Guidance:** Optionally uses an AI advisor (GPT-4o-mini) to suggest better parameters when the optimizer gets stuck. This is completely optional and OFF by default.

---

## Processing Log

After processing, this collapsible panel shows exactly what happened at each step. Use it to understand which settings had the biggest impact and adjust accordingly.
