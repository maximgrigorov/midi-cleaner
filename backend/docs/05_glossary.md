# Glossary

Plain-language definitions of terms used in this tool.

---

**AI MIDI Transcription Noise**
When an AI tool converts audio to MIDI, it sometimes "hears" notes that aren't really there, or writes existing notes with slightly wrong timing, pitch, or duration. These errors are called "transcription noise." They show up as extra notes, overlapping notes, or tiny artifacts in the MIDI file.

Imagine having someone transcribe a conversation by ear — they might mishear words, write the same word twice, or add extra spaces. MIDI transcription noise is the musical equivalent.

---

**CC (Control Change)**
MIDI messages that carry non-note information. The most common ones are:
- **CC#64 (Sustain Pedal):** Tells the instrument to sustain all played notes, like pressing the damper pedal on a piano
- **CC#68 (Legato):** Tells the instrument to play notes smoothly connected

For notation purposes, CC messages are usually not needed and can be safely removed.

---

**Channel**
MIDI files can carry up to 16 separate "channels" (numbered 0–15). Each channel typically represents a different instrument or voice. Channel 10 (sometimes shown as 9 in 0-indexed tools) is traditionally reserved for drums.

---

**Overlap**
When one note starts before the previous note on the same pitch has ended. In sheet music, this forces notation software to create a second "voice" to represent both notes simultaneously. Most overlaps in AI-transcribed MIDI are errors.

---

**Pitch**
How high or low a note sounds. In MIDI, pitches are numbered 0–127, where 60 is Middle C. Each number is one semitone (half step) apart.

---

**Polyphony**
Multiple notes sounding at the same time. A piano chord is polyphonic. A single sung note is monophonic. Legitimate polyphony (like string chords) should be preserved; artificial polyphony from transcription errors should be removed.

---

**Quantization**
Snapping note timing to an exact rhythmic grid. Like auto-tune for rhythm — it makes notes land exactly on the beat instead of slightly before or after. Useful for cleaning up messy timing, but can remove natural "feel" (rubato, swing).

---

**Ticks**
The basic unit of time in a MIDI file. The number of ticks per quarter note (TPB, or "ticks per beat") is set in the file header — typically 480. So at TPB=480:
- Quarter note = 480 ticks
- Eighth note = 240 ticks
- Sixteenth note = 120 ticks

When you set "Min Duration = 120 ticks," you're removing notes shorter than a sixteenth note.

---

**Track**
A MIDI file can contain multiple tracks, each representing a different instrument part. Track 0 is usually the "conductor track" containing tempo and time signature information. Other tracks contain note data.

---

**Triplet**
Three notes played in the time normally occupied by two notes of the same value. For example, three eighth-note triplets fit in the space of two regular eighth notes. AI transcription sometimes creates triplet-like note durations when the original music was straight.

---

**Velocity**
How hard a note is played, on a scale of 0–127. Higher velocity = louder. In real performance, velocity varies naturally. AI transcription sometimes creates very quiet (low velocity) ghost notes that aren't part of the actual performance.

---

**Voice**
In notation software, a "voice" is an independent musical line that shares the same staff. A staff can have up to 4 voices, shown with different stem directions. When MIDI has overlapping notes or mismatched durations, notation software creates extra voices, making the score hard to read.

The main goal of this tool is to reduce unnecessary voices while keeping the music intact.
