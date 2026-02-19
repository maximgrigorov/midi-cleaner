"""Noise Filter — removes parasitic short notes and low-velocity artifacts.

Particularly useful for AI-transcribed MIDI (e.g. from Suno) where distorted
guitar tracks contain many spurious very-short or very-quiet notes.

Configurable thresholds:
  - min_duration_ticks: minimum note length in ticks (default: 120)
  - min_velocity: minimum MIDI velocity 0-127 (default: 20)
"""

from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
)


class NoiseFilter:
    """Remove short and quiet parasitic notes."""

    def __init__(self, config):
        self.enabled = config.get('filter_noise', True)
        self.min_duration = config.get('min_duration_ticks', 120)
        self.min_velocity = config.get('min_velocity', 20)

    def process(self, track, ticks_per_beat):
        """Process a single track: remove notes below thresholds.

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

        original_count = len(note_pairs)

        # Filter by duration and velocity
        filtered = [
            n for n in note_pairs
            if self._keep_note(n)
        ]

        removed_count = original_count - len(filtered)
        if removed_count > 0:
            # Store stats for reporting (not used in output, just for logging)
            pass

        return rebuild_track_from_pairs(filtered, non_notes)

    def _keep_note(self, note):
        """Decide whether to keep a note based on duration and velocity thresholds."""
        duration = note['offset'] - note['onset']
        if duration < self.min_duration:
            return False
        if note['velocity'] < self.min_velocity:
            return False
        return True
