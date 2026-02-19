"""Merge Tracks To Single Track — flattens multi-track MIDI into one MTrk.

Useful when preparing AI-transcribed MIDI for manual cleanup in a notation
editor: having all events on a single track makes it easier to see the full
picture and delete artefacts without switching between tracks.

The processor preserves exact timing, velocities, channels, and all meta
events.  CC events are excluded by default but can be selectively included
via a whitelist.

Config (nested under 'merge_tracks' key):
    enabled       (bool,       default False) — enable/disable processor
    include_cc    (bool,       default False) — include CC events in output
    cc_whitelist  (list[int],  default [64, 68]) — CC numbers to keep when
                  include_cc is True; empty list = keep all CC
"""

import mido

from utils.midi_helpers import to_absolute_time


class MergeTracksToSingleTrack:
    """Flatten a multi-track MIDI file into a single-track (Type 0) file.

    All tracks are merged into one MTrk with events ordered by absolute tick.
    At the same tick the ordering is: meta → note_off → other → note_on,
    which prevents stuck notes and keeps notation stable.
    """

    def __init__(self, config: dict) -> None:
        cfg = config.get('merge_tracks', {})
        self.enabled: bool = cfg.get('enabled', False)
        self.include_cc: bool = cfg.get('include_cc', False)
        self.cc_whitelist: set[int] = set(cfg.get('cc_whitelist', [64, 68]))

    def process(self, midi_file):
        """Merge all tracks of a MIDI file into a single track.

        Args:
            midi_file: mido.MidiFile (multi-track)

        Returns:
            mido.MidiFile — Type 0 file with one track (or original when disabled)
        """
        if not self.enabled:
            return midi_file

        tpb = midi_file.ticks_per_beat

        # Collect events from every track in absolute time
        all_events: list[tuple[int, mido.Message]] = []

        for track in midi_file.tracks:
            abs_msgs = to_absolute_time(track)
            for abs_time, msg in abs_msgs:
                # Skip per-track end markers; we'll add one at the end
                if msg.type == 'end_of_track':
                    continue
                if not self._should_include(msg):
                    continue
                all_events.append((abs_time, msg))

        # Stable sort: time → event-type priority
        all_events.sort(key=self._sort_key)

        # Build the single merged track with delta times
        new_track = mido.MidiTrack()
        prev_time = 0
        for abs_time, msg in all_events:
            delta = max(0, int(round(abs_time - prev_time)))
            new_track.append(msg.copy(time=delta))
            prev_time = abs_time

        new_track.append(mido.MetaMessage('end_of_track', time=0))

        # Single-track file is Type 0 by convention
        output = mido.MidiFile(type=0, ticks_per_beat=tpb)
        output.tracks.append(new_track)
        return output

    # ── internal ────────────────────────────────────────────────────────────

    def _should_include(self, msg) -> bool:
        """Decide whether an event belongs in the merged output."""
        if msg.is_meta:
            return True
        if msg.type in ('note_on', 'note_off'):
            return True
        if msg.type == 'control_change':
            if not self.include_cc:
                return False
            # Empty whitelist means include all CC
            if not self.cc_whitelist:
                return True
            return msg.control in self.cc_whitelist
        # Other channel messages (program_change, pitch_wheel, etc.)
        return True

    @staticmethod
    def _sort_key(item: tuple[int, mido.Message]) -> tuple[int, int]:
        """Sort events at the same tick: meta → note_off → other → note_on."""
        t, msg = item
        if msg.is_meta:
            order = 0
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            order = 1
        elif msg.type == 'note_on':
            order = 3
        else:
            order = 2
        return (t, order)
