# Troubleshooting

Common problems and how to fix them.

---

## Guitar Pro shows multiple voices after cleaning

**Likely cause:** There are still overlapping notes on the same pitch.

**Fix:**
- Make sure **Same-Pitch Overlap Resolver** is ON
- Make sure **Merge Voices** is ON
- Try the **"FX / Cleaner"** preset which is more aggressive
- Check the Processing Log — look at the "SamePitchOverlapResolver" row and see if it removed any notes

---

## Too many notes were removed

**Likely cause:** The Noise Filter thresholds are too high.

**Fix:**
- Lower **Min Note Duration** (try 60 instead of 120)
- Lower **Min Velocity** (try 5 instead of 20)
- Check if **Remove Triplets** is ON when it shouldn't be (this can remove real musical content in swing or jazz pieces)

---

## The score has tempo markings everywhere (♩=87, ♩=91...)

**Likely cause:** Duplicate tempo events in data tracks.

**Fix:**
- Make sure **Deduplicate Tempo** is ON — this removes the redundant tempo events that cause this

---

## Guitar Pro shows wrong note durations

**Likely cause:** Notes within chords have different durations, forcing Guitar Pro to create separate voices.

**Fix:**
- Make sure **Merge Voices** is ON — this includes final chord alignment which gives all notes in a chord the same duration
- If you see very long and very short notes mixed together, try increasing **Min Duration**

---

## The melody sounds different after cleaning

**Likely cause:** Cleaning removed notes that were part of the original performance.

**Fix:**
- Use a "Preserve" preset instead of "Cleaner"
- Lower Min Duration and Min Velocity
- Turn OFF Quantize and Remove Triplets
- Check the Processing Log to identify which step removed the most notes, and relax that setting

---

## Auto-Tune takes too long

**Fix:**
- Reduce **Max Trials** to 15–20 instead of 40
- This is still enough to find good parameters, just less exhaustive

---

## The file won't upload

**Possible causes:**
- File is not a valid `.mid` or `.midi` file
- File is too large (max 16 MB)
- The file was created by a tool that writes non-standard MIDI

**Fix:**
- Try opening the file in another MIDI editor and re-saving it
- Check that the file extension is `.mid` or `.midi`

---

## Nothing changes after processing

**Likely cause:** All processors are disabled, or the file is already clean.

**Fix:**
- Check that at least some toggles are ON
- Look at the Processing Log — if "Notes Removed" is 0 for every step, the file may already be clean
- Try enabling more aggressive settings

---

## When to stop cleaning

This is the most important skill to develop. Here are guidelines:

1. **Listen to the result** — if it sounds like the original, you're done
2. **Check the note count** — if you've removed more than 30–40% of notes, you may be over-cleaning
3. **Look at the score** — if the notation in Guitar Pro looks reasonable (correct rhythms, no voice splits), stop
4. **Compare original and processed** — use the Player's "Original" / "Processed" toggle to listen to both

The goal is not a "perfect" MIDI file — it's a MIDI file that opens cleanly in your notation software while preserving the musical intent.
