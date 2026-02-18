"""Tempo Deduplicator — removes redundant set_tempo meta events.

AI-transcribed MIDI files often contain hundreds of identical set_tempo events
scattered across every bar, causing notation software (Guitar Pro, MuseScore)
to display spurious tempo markings like ♩=91 on every bar line.

This processor keeps the first set_tempo event and removes all subsequent ones
that repeat the same tempo value.  Real tempo changes (different BPM) are
preserved with their original timing intact.

Config (nested under 'tempo_deduplicator' key):
    enabled  (bool, default True)  — enable/disable processor
"""

import mido

from utils.midi_helpers import to_absolute_time, to_delta_time


class TempoDeduplicator:
    """Remove consecutive duplicate set_tempo meta events from a track.

    Keeps the first occurrence of each tempo value and removes any subsequent
    set_tempo whose value matches the most recently kept one.  Events at the
    same tick with identical tempo are also collapsed to a single event.
    """

    def __init__(self, config: dict) -> None:
        cfg = config.get('tempo_deduplicator', {})
        self.enabled: bool = cfg.get('enabled', True)

    def process(self, track, ticks_per_beat: int):
        """Process a single track: remove redundant set_tempo events.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution (unused, kept for API consistency)

        Returns:
            mido.MidiTrack — processed track (original returned when disabled)
        """
        if not self.enabled:
            return track

        abs_msgs = to_absolute_time(track)

        # Walk events, tracking the last kept tempo value
        last_tempo = None
        filtered = []

        for abs_time, msg in abs_msgs:
            if msg.type == 'set_tempo':
                if msg.tempo == last_tempo:
                    # Duplicate of the most recently kept tempo — skip
                    continue
                # Real tempo change (or the very first set_tempo) — keep
                last_tempo = msg.tempo
            filtered.append((abs_time, msg))

        # Convert back to delta time and build a new track
        result_msgs = to_delta_time(filtered)
        new_track = mido.MidiTrack()
        new_track.extend(result_msgs)
        return new_track
