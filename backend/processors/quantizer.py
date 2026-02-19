"""Quantizer — snaps note onset times and durations to the nearest grid position.

Bar-aware: ensures notes do not cross bar boundaries, which would cause
Guitar Pro to display red bars or add spurious tempo changes.

Supports quarter, eighth, sixteenth, and thirty-second note grids.
Default grid is eighth notes (2 divisions per beat).
"""

from config import GRID_DIVISORS
from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
    get_time_signature,
    calculate_bar_ticks,
)


class Quantizer:
    """Snap note timing to the nearest rhythmic grid, respecting bar boundaries."""

    def __init__(self, config):
        self.enabled = config.get('quantize', True)
        self.grid_name = config.get('quantize_grid', 'eighth')

    def process(self, track, ticks_per_beat, time_sig=(4, 4)):
        """Process a single track: quantize note onset times and durations.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution
            time_sig: (numerator, denominator) tuple

        Returns:
            mido.MidiTrack — processed track
        """
        if not self.enabled:
            return track

        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)

        if not note_pairs:
            return track

        divisor = GRID_DIVISORS.get(self.grid_name, 2)
        grid_ticks = ticks_per_beat / divisor  # ticks per grid unit
        bar_ticks = calculate_bar_ticks(ticks_per_beat, time_sig)

        quantized = []
        for note in note_pairs:
            # Quantize onset
            quantized_onset = self._snap_to_grid(note['onset'], grid_ticks)

            # Quantize duration (minimum 1 grid unit)
            original_duration = note['offset'] - note['onset']
            quantized_duration = self._quantize_duration(original_duration, grid_ticks)

            quantized_offset = quantized_onset + quantized_duration

            # Clip to bar boundary: note must not cross into the next bar
            bar_start = (quantized_onset // bar_ticks) * bar_ticks
            bar_end = bar_start + bar_ticks

            if quantized_offset > bar_end:
                quantized_offset = bar_end
                quantized_duration = quantized_offset - quantized_onset

            # Ensure minimum duration of 1 grid unit after clipping
            min_dur = max(1, int(round(grid_ticks)))
            if quantized_duration < min_dur:
                # Skip notes that become too short after clipping
                continue

            note['onset'] = quantized_onset
            note['offset'] = quantized_offset
            quantized.append(note)

        return rebuild_track_from_pairs(quantized, non_notes)

    def _snap_to_grid(self, tick, grid_ticks):
        """Snap a tick position to the nearest grid point."""
        if grid_ticks <= 0:
            return tick
        grid_int = int(round(grid_ticks))
        return int(round(tick / grid_int)) * grid_int

    def _quantize_duration(self, duration, grid_ticks):
        """Quantize a note duration to the nearest grid multiple (minimum 1 unit)."""
        if grid_ticks <= 0:
            return duration
        grid_int = int(round(grid_ticks))
        units = max(1, round(duration / grid_ticks))
        return units * grid_int
