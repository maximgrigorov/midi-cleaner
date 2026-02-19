export const TOOLTIPS: Record<string, string> = {
  tempo_deduplicator:
    "AI transcription tools often write the tempo marker hundreds of times. This removes the duplicates so notation software doesn't clutter your score.",
  merge_voices:
    'Reduces unnecessary "voices" in the staff. Use ON for melody and bass; OFF for piano or strings where multiple voices are intentional.',
  remove_overlaps:
    'Notes that start before the previous one ends force notation software to create extra voices. Almost always safe to enable.',
  same_pitch_overlap_resolver:
    'When two identical notes overlap, keeps the better one (longer duration wins) and removes the other.',
  filter_noise:
    'Removes notes that are too short or too quiet to be real — the musical equivalent of background noise.',
  min_duration_ticks:
    'Notes shorter than this are removed. 120 ticks ≈ a sixteenth note. 240 ticks ≈ an eighth note.',
  min_velocity:
    'Notes quieter than this (0–127 scale) are removed. Default 20 catches ghost notes without touching real ones.',
  remove_triplets:
    'Converts triplet-like note durations back to straight rhythms. Turn OFF for jazz or swing.',
  triplet_tolerance:
    'How aggressively to detect triplets. Higher = catches more, but may incorrectly convert some notes.',
  quantize:
    'Snaps note timing to a rhythmic grid. Makes scores look cleaner but may remove expressive timing. Turn OFF for rubato or FX.',
  quantize_grid:
    'The rhythmic grid size for quantization. Eighth note works for most music.',
  remove_cc:
    'Strips sustain pedal (CC#64) and legato (CC#68) data. Good for notation cleanup; turn OFF if you need realistic MIDI playback.',
  pitch_cluster:
    'Merges notes that are very close in both pitch and time — likely transcription noise, not real notes.',
  time_window_ticks:
    'How close in time two notes must be (in ticks) to be considered simultaneous.',
  pitch_threshold:
    'How many semitones apart two notes can be and still get merged. 1 = merge if within one semitone.',
  start_bar:
    "Skip the first N bars. Useful if you've already cleaned part of the file.",
  merge_tracks:
    'Combines all tracks into one (Type 0 MIDI). Loses track separation — use only if specifically needed.',
  llm: 'Uses an AI model to suggest better parameters when the optimizer gets stuck. Optional; uses your local LLM endpoint.',
  auto_optimize:
    'Automatically tries many parameter combinations and picks the one that produces the cleanest score. Takes 1–2 minutes.',
};
