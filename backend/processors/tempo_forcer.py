"""Tempo Forcer — forces all tracks to a single fixed BPM.

When combining MIDI files from different sources (e.g. Suno + Klang.io),
divergent tempo maps cause tracks to desync in notation software like
Guitar Pro.  This processor removes ALL set_tempo meta events from every
track and inserts a single set_tempo event at tick 0 in the conductor
track (tracks[0]).

Config (top-level key):
    force_bpm  (float | None, default None)  — target BPM; None = disabled
"""

import mido


class TempoForcer:
    """Replace the entire tempo map with a single fixed BPM.

    Removes every set_tempo event from all tracks and places one
    set_tempo at tick 0 in tracks[0].
    """

    def __init__(self, target_bpm: float) -> None:
        self.target_bpm = target_bpm
        self.tempo_events_removed = 0

    def process(self, midi_file):
        """Process an entire MIDI file in-place.

        Args:
            midi_file: mido.MidiFile (already a working copy)

        Returns:
            mido.MidiFile — the same object, modified
        """
        target_tempo = mido.bpm2tempo(self.target_bpm)
        removed = 0

        for track in midi_file.tracks:
            new_track = mido.MidiTrack()
            abs_time = 0
            prev_abs = 0

            for msg in track:
                abs_time += msg.time
                if msg.type == 'set_tempo':
                    removed += 1
                    continue
                delta = max(0, int(round(abs_time - prev_abs)))
                new_track.append(msg.copy(time=delta))
                prev_abs = abs_time

            track.clear()
            track.extend(new_track)

        self.tempo_events_removed = removed

        # Insert a single set_tempo at tick 0 in the conductor track
        if midi_file.tracks:
            midi_file.tracks[0].insert(
                0, mido.MetaMessage('set_tempo', tempo=target_tempo, time=0)
            )

        return midi_file
