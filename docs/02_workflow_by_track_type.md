# Workflow by Track Type

Different instruments need different cleaning strategies. Here are step-by-step recipes for each.

---

## FX / Sound Effects

AI transcription of FX tracks tends to produce many short "ghost" notes and overlapping notes on the same pitch. This causes Guitar Pro to split the part into multiple voices.

### Recipe: FX Cleanup

1. Select preset **"FX / Preserve"** (gentle) or **"FX / Cleaner"** (aggressive)
2. Make sure **Same-Pitch Overlap Resolver** is ON
3. Set **Min Note Duration** between 60–120 ticks
4. Set **Min Velocity** to 3–10
5. **Pitch Cluster** ON, window 15–30 ticks, threshold 1 semitone
6. Process and check the log — look at "Notes Removed" count
7. If too many notes vanished, lower Min Duration; if still noisy, raise it

### When to Stop

If your cleaned MIDI plays back the same melody you hear in the original, stop cleaning. Further tweaking will start removing real musical content.

---

## Strings / Orchestral

String parts are often polyphonic (multiple notes at once). Be careful not to remove legitimate chords.

### Recipe: Strings Cleanup

1. Select preset **"Strings / Preserve"**
2. Keep **Merge Voices** OFF if you want to preserve polyphony
3. Set **Pitch Cluster** threshold to 1 (only merge very close pitches)
4. Set **Min Duration** to 80–120 ticks
5. Keep **Quantize** OFF unless the timing is very messy

### When to Stop

If the chord structure looks right in your notation software, you're done. Strings naturally have many simultaneous notes — that's normal.

---

## Vocals / Melody

Vocal transcriptions should be monophonic (one note at a time). Any "extra" notes are almost certainly noise.

### Recipe: Vocals Cleanup

1. Select preset **"Vocals / Preserve"**
2. **Merge Voices** ON — vocals should be a single line
3. **Same-Pitch Overlap Resolver** ON
4. **Pitch Cluster** threshold 0 (only merge exact same pitch)
5. **Min Duration** 60 ticks (vocals can have short notes)
6. **Min Velocity** low (5) — even quiet notes may be real

### When to Stop

When you see a single clean melody line without overlapping notes or stray pitches.

---

## Guitar

Guitar parts often have both single-note lines and chords. The cleaner needs to preserve this variety.

### Recipe: Guitar Cleanup

1. Select preset **"Guitar / Preserve"**
2. **Min Duration** 100 ticks (removes most ghost notes)
3. **Pitch Cluster** ON, window 20 ticks, threshold 1
4. **Remove CC** ON — guitar MIDI rarely needs sustain pedal data
5. **Same-Pitch Overlap Resolver** ON

### When to Stop

When both single-note passages and chord sections look correct in notation. If chords lost notes, lower Min Duration.

---

## Bass

Bass parts are similar to vocals — mostly single notes, but with longer durations.

### Recipe: Bass Cleanup

1. Select preset **"Bass / Preserve"**
2. **Min Duration** 100–150 ticks (bass notes are typically longer)
3. **Min Velocity** 12 (bass tends to be played firmly)
4. **Merge Voices** ON
5. **Pitch Cluster** ON, threshold 1

### When to Stop

When you see a clean single-note line with no obvious ghost notes.

---

## Drums / Percussion

Drums are very different from pitched instruments. Notes are very short, and every hit matters.

### Recipe: Drums Cleanup

1. Select preset **"Drums / Preserve"**
2. **Min Duration** very low (30 ticks) — drum hits are naturally short
3. **Pitch Cluster** OFF — each pitch represents a different drum
4. **Merge Voices** OFF — drums typically use channel 10
5. **Quantize** only if the timing feels sloppy

### When to Stop

When each drum hit appears once in the right place. Over-cleaning drums makes them sound mechanical.
