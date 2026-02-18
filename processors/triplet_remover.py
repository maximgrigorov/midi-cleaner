"""Triplet Remover — detects and converts triplet note durations to straight eighths.

Triplet durations (in ticks at PPQ=480):
  - Triplet quarter:    320  (480 * 2/3)
  - Triplet eighth:     160  (240 * 2/3)
  - Triplet sixteenth:   80  (120 * 2/3)

All detected triplet notes are converted to eighth-note duration (ticks_per_beat / 2).
"""

from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
)


class TripletRemover:
    """Detect triplet note durations and convert them to straight eighth notes."""

    def __init__(self, config):
        self.enabled = config.get('remove_triplets', True)
        self.tolerance = config.get('triplet_tolerance', 0.15)

    def process(self, track, ticks_per_beat):
        """Process a single track: find and convert triplet notes.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution

        Returns:
            mido.MidiTrack — processed track
        """
        if not self.enabled:
            return track

        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)

        if not note_pairs:
            return track

        eighth_ticks = ticks_per_beat / 2

        # Build list of triplet reference durations
        triplet_durations = self._get_triplet_durations(ticks_per_beat)

        converted_count = 0
        for note in note_pairs:
            duration = note['offset'] - note['onset']
            if self._is_triplet(duration, triplet_durations):
                # Convert to eighth note duration
                note['offset'] = note['onset'] + int(round(eighth_ticks))
                converted_count += 1

        return rebuild_track_from_pairs(note_pairs, non_notes)

    def _get_triplet_durations(self, tpb):
        """Calculate expected triplet durations for common note values.

        Returns list of (triplet_ticks, description) tuples.
        """
        return [
            (tpb * 4 / 3, 'triplet_half'),          # triplet half note
            (tpb * 2 / 3, 'triplet_quarter'),        # triplet quarter note
            (tpb / 3, 'triplet_eighth'),              # triplet eighth note
            (tpb / 6, 'triplet_sixteenth'),           # triplet sixteenth note
        ]

    def _is_triplet(self, duration, triplet_durations):
        """Check if a note duration matches any known triplet duration."""
        for triplet_ticks, _ in triplet_durations:
            if triplet_ticks <= 0:
                continue
            relative_error = abs(duration - triplet_ticks) / triplet_ticks
            if relative_error <= self.tolerance:
                return True
        return False
