"""Unit tests for PitchClusterProcessor.

Covers:
  - Clustered notes are collapsed to a single winner (note count decreases)
  - Notes too far apart in pitch or time are left untouched
  - Disabled processor returns the track byte-for-byte identical
"""

import sys
import os

# Ensure project root is importable when running pytest from any directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from processors.pitch_cluster import PitchClusterProcessor
from utils.midi_helpers import extract_note_pairs


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_track(*notes: dict) -> mido.MidiTrack:
    """Build a minimal MidiTrack from a list of note dicts.

    Each dict must have: pitch, channel, velocity, onset, offset  (absolute ticks).
    """
    # Collect all events as (abs_time, msg)
    events: list[tuple[int, mido.Message]] = []
    for n in notes:
        events.append((n['onset'], mido.Message(
            'note_on', channel=n['channel'], note=n['pitch'],
            velocity=n['velocity'], time=0,
        )))
        events.append((n['offset'], mido.Message(
            'note_off', channel=n['channel'], note=n['pitch'],
            velocity=0, time=0,
        )))

    events.sort(key=lambda e: (e[0], 0 if e[1].type == 'note_off' else 1))

    track = mido.MidiTrack()
    prev = 0
    for abs_t, msg in events:
        track.append(msg.copy(time=abs_t - prev))
        prev = abs_t
    track.append(mido.MetaMessage('end_of_track', time=0))
    return track


def _note(pitch: int, onset: int, offset: int,
          velocity: int = 80, channel: int = 0) -> dict:
    return dict(pitch=pitch, onset=onset, offset=offset,
                velocity=velocity, channel=channel)


# ── default config ───────────────────────────────────────────────────────────

DEFAULT_CFG = {'pitch_cluster': {'enabled': True, 'time_window_ticks': 80, 'pitch_threshold': 1}}
DISABLED_CFG = {'pitch_cluster': {'enabled': False}}


# ── tests ────────────────────────────────────────────────────────────────────

class TestPitchClusterProcessor:

    def test_cluster_reduces_note_count(self):
        """Three notes within onset window and pitch threshold → collapsed to one."""
        # All start at tick 0 (well within 80-tick window), pitches 60/61/60 (≤1 semitone)
        track = _make_track(
            _note(60, onset=0,  offset=480),
            _note(61, onset=10, offset=480),
            _note(60, onset=20, offset=480),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 1, f"Expected 1 note after clustering, got {len(pairs)}"

    def test_winner_selection_highest_velocity(self):
        """Among clustered notes the one with highest velocity survives."""
        track = _make_track(
            _note(60, onset=0,  offset=480, velocity=64),
            _note(61, onset=5,  offset=480, velocity=100),  # ← winner
            _note(60, onset=10, offset=480, velocity=40),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 1
        assert pairs[0]['velocity'] == 100

    def test_winner_selection_longest_duration_tiebreak(self):
        """When velocity is tied, the note with the longest duration survives."""
        track = _make_track(
            _note(60, onset=0,  offset=240, velocity=80),   # short
            _note(61, onset=5,  offset=960, velocity=80),   # long ← winner
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 1
        assert pairs[0]['offset'] - pairs[0]['onset'] == 960 - 5

    def test_distant_pitches_untouched(self):
        """Notes beyond pitch_threshold semitones apart are NOT merged."""
        # pitch 60 and pitch 63 are 3 semitones apart → outside threshold of 1
        track = _make_track(
            _note(60, onset=0,  offset=480),
            _note(63, onset=5,  offset=480),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 2, "Distant-pitch notes should not be merged"

    def test_distant_onsets_untouched(self):
        """Notes whose onset gap exceeds time_window_ticks are NOT merged."""
        # Same pitch but 200 ticks apart → beyond 80-tick window
        track = _make_track(
            _note(60, onset=0,   offset=480),
            _note(60, onset=200, offset=680),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 2, "Temporally distant notes should not be merged"

    def test_different_channels_not_merged(self):
        """Notes on different MIDI channels must never be merged."""
        track = _make_track(
            _note(60, onset=0, offset=480, channel=0),
            _note(60, onset=5, offset=480, channel=1),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 2, "Notes on different channels must remain separate"

    def test_disabled_returns_identical_track(self):
        """When enabled=False the processor must return the track unchanged."""
        track = _make_track(
            _note(60, onset=0,  offset=480),
            _note(61, onset=5,  offset=480),
            _note(62, onset=10, offset=480),
        )
        proc = PitchClusterProcessor(DISABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)
        # Exact same object returned when disabled
        assert result is track

    def test_empty_track_passthrough(self):
        """An empty track (no notes) must be returned without error."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('end_of_track', time=0))
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        assert extract_note_pairs(result) == []

    def test_large_cluster_multiple_winners(self):
        """Two separate clusters on the same channel each collapse to one note."""
        # Cluster A: pitches 60/61 near onset 0
        # Cluster B: pitches 72/73 near onset 1000 (far from cluster A in time)
        track = _make_track(
            _note(60, onset=0,    offset=480),
            _note(61, onset=10,   offset=480),
            _note(72, onset=1000, offset=1480),
            _note(73, onset=1010, offset=1480),
        )
        proc = PitchClusterProcessor(DEFAULT_CFG)
        result = proc.process(track, ticks_per_beat=480)
        pairs = extract_note_pairs(result)
        assert len(pairs) == 2, "Two independent clusters should each yield one note"
