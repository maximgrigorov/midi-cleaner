"""Same-Pitch Overlap Resolver — ensures at most one active note per (channel, pitch).

Guitar Pro creates multiple "voices" when MIDI contains overlapping notes of the
same pitch on the same channel.  This processor removes the shorter/weaker
duplicate, preserving the note that best represents the original performance feel.

Selection rule when two notes overlap:
  1. Keep the note with the LONGER duration.
  2. Tie-break: higher velocity wins.
  3. Still tied: earlier-starting note wins.

The losing note is removed entirely (no trimming or splitting).

Config:
    same_pitch_overlap_resolver:
        enabled: true       (default True)
"""

from collections import defaultdict
from typing import Any

from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
)


class SamePitchOverlapResolver:
    """Remove overlapping same-pitch notes within each (channel, pitch) group."""

    def __init__(self, config: dict) -> None:
        cfg = config.get('same_pitch_overlap_resolver', {})
        self.enabled: bool = cfg.get('enabled', True)

    def process(self, track, ticks_per_beat: int):
        """Process a single track: resolve same-pitch overlaps.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution (unused, kept for API consistency)

        Returns:
            mido.MidiTrack — processed track
        """
        if not self.enabled:
            return track

        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)

        if not note_pairs:
            return track

        by_key: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
        for note in note_pairs:
            by_key[(note['channel'], note['pitch'])].append(note)

        result: list[dict[str, Any]] = []
        for notes in by_key.values():
            result.extend(self._resolve_group(notes))

        result.sort(key=lambda n: (n['onset'], n['pitch']))
        return rebuild_track_from_pairs(result, non_notes)

    def _resolve_group(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Resolve overlaps within a single (channel, pitch) group.

        Greedy sweep: process notes in start-time order.  When the current
        note overlaps with the previously kept note, compare them using the
        selection rule and discard the loser.
        """
        sorted_notes = sorted(notes, key=lambda n: (n['onset'], n['offset']))
        kept: list[dict[str, Any]] = []

        for note in sorted_notes:
            if not kept:
                kept.append(note)
                continue

            last = kept[-1]
            if note['onset'] < last['offset']:
                winner = self._pick_winner(last, note)
                if winner is not last:
                    kept[-1] = winner
            else:
                kept.append(note)

        return kept

    @staticmethod
    def _pick_winner(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
        """Return the note to keep when *a* and *b* overlap.

        Priority: longer duration > higher velocity > earlier onset.
        """
        dur_a = a['offset'] - a['onset']
        dur_b = b['offset'] - b['onset']
        if dur_a != dur_b:
            return a if dur_a > dur_b else b
        if a['velocity'] != b['velocity']:
            return a if a['velocity'] > b['velocity'] else b
        return a if a['onset'] <= b['onset'] else b
