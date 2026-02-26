"""Unit tests for TempoForcer.

Covers:
  - All set_tempo events are removed and replaced with a single one
  - The single set_tempo is at tick 0 in tracks[0]
  - Note timing is preserved after tempo replacement
  - Telemetry reports correct count of removed events
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from processors.tempo_forcer import TempoForcer
from utils.midi_helpers import analyze_tempo_map


# ── helpers ─────────────────────────────────────────────────────────────────

TEMPO_120 = mido.bpm2tempo(120)  # 500000
TEMPO_100 = mido.bpm2tempo(100)  # 600000
TEMPO_90 = mido.bpm2tempo(90)


def _tempo_events(midi_file) -> list[tuple[int, int, int]]:
    """Extract (track_idx, abs_tick, tempo_value) for every set_tempo."""
    result = []
    for idx, track in enumerate(midi_file.tracks):
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            if msg.type == 'set_tempo':
                result.append((idx, abs_time, msg.tempo))
    return result


def _make_midi(tracks_data, tpb=480):
    """Build a mido.MidiFile from a list of track message lists."""
    mid = mido.MidiFile(type=1, ticks_per_beat=tpb)
    for msgs in tracks_data:
        track = mido.MidiTrack()
        track.extend(msgs)
        mid.tracks.append(track)
    return mid


# ── tests ────────────────────────────────────────────────────────────────────

class TestTempoForcer:

    def test_replaces_all_tempos_with_single(self):
        """Multiple set_tempo events across tracks → single one at tick 0."""
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=0),
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_90, time=0),
                mido.Message('note_on', channel=0, note=60, velocity=80, time=0),
                mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
        ])

        forcer = TempoForcer(target_bpm=120.0)
        result = forcer.process(mid)

        tempos = _tempo_events(result)
        assert len(tempos) == 1, f"Expected 1 set_tempo, got {len(tempos)}"
        assert tempos[0][0] == 0, "set_tempo must be in track 0"
        assert tempos[0][1] == 0, "set_tempo must be at tick 0"
        assert tempos[0][2] == TEMPO_120

    def test_note_timing_preserved(self):
        """Notes must retain their original tick positions."""
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=0),
                mido.MetaMessage('end_of_track', time=0),
            ],
            [
                mido.Message('note_on', channel=0, note=60, velocity=80, time=0),
                mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
                mido.Message('note_on', channel=0, note=62, velocity=80, time=0),
                mido.Message('note_off', channel=0, note=62, velocity=0, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
        ])

        forcer = TempoForcer(target_bpm=130.0)
        result = forcer.process(mid)

        # Check note timing in track 1
        track = result.tracks[1]
        abs_time = 0
        note_ons = []
        for msg in track:
            abs_time += msg.time
            if msg.type == 'note_on':
                note_ons.append((abs_time, msg.note))

        assert note_ons == [(0, 60), (480, 62)]

    def test_telemetry_count(self):
        """tempo_events_removed reports the correct count."""
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=0),
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480),
                mido.MetaMessage('set_tempo', tempo=TEMPO_90, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
        ])

        forcer = TempoForcer(target_bpm=120.0)
        forcer.process(mid)

        assert forcer.tempo_events_removed == 3

    def test_empty_file(self):
        """A MIDI file with no tracks should not crash."""
        mid = mido.MidiFile(type=1, ticks_per_beat=480)

        forcer = TempoForcer(target_bpm=120.0)
        result = forcer.process(mid)

        assert len(result.tracks) == 0

    def test_no_tempo_events(self):
        """A file with no set_tempo should get exactly one inserted."""
        mid = _make_midi([
            [
                mido.Message('note_on', channel=0, note=60, velocity=80, time=0),
                mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
        ])

        forcer = TempoForcer(target_bpm=140.0)
        result = forcer.process(mid)

        tempos = _tempo_events(result)
        assert len(tempos) == 1
        assert tempos[0][2] == mido.bpm2tempo(140.0)
        assert forcer.tempo_events_removed == 0

    def test_target_bpm_precision(self):
        """The inserted tempo must match the requested BPM exactly."""
        mid = _make_midi([
            [mido.MetaMessage('end_of_track', time=0)],
        ])

        for bpm in [40.0, 72.5, 120.0, 200.0, 300.0]:
            forcer = TempoForcer(target_bpm=bpm)
            result = forcer.process(mid)
            tempos = _tempo_events(result)
            assert tempos[0][2] == mido.bpm2tempo(bpm)


class TestAnalyzeTempoMap:

    def test_no_tempo_events_returns_120(self):
        """A file with no set_tempo defaults to 120 BPM."""
        mid = _make_midi([
            [
                mido.Message('note_on', channel=0, note=60, velocity=80, time=0),
                mido.Message('note_off', channel=0, note=60, velocity=0, time=480),
                mido.MetaMessage('end_of_track', time=0),
            ],
        ])
        assert analyze_tempo_map(mid) == 120.0

    def test_single_tempo_event(self):
        """A file with one set_tempo returns that BPM."""
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0),
                mido.MetaMessage('end_of_track', time=960),
            ],
        ])
        assert analyze_tempo_map(mid) == 120.0

    def test_dominant_tempo_wins(self):
        """The tempo spanning the most ticks is returned."""
        # 120 BPM for ticks 0-480 (480 ticks), then 100 BPM for ticks 480-1920 (1440 ticks)
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0),
                mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=480),
                mido.MetaMessage('end_of_track', time=1440),
            ],
        ])
        assert analyze_tempo_map(mid) == 100.0

    def test_empty_file(self):
        """An empty file defaults to 120 BPM."""
        mid = mido.MidiFile(type=1, ticks_per_beat=480)
        assert analyze_tempo_map(mid) == 120.0

    def test_duplicate_tempos_summed(self):
        """Same tempo at multiple points sums their spans."""
        # 120 BPM: ticks 0-480, then 100 BPM: ticks 480-960, then 120 BPM: ticks 960-1920
        # 120 BPM spans 480 + 960 = 1440 ticks, 100 BPM spans 480 ticks → 120 wins
        mid = _make_midi([
            [
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0),
                mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=480),
                mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480),
                mido.MetaMessage('end_of_track', time=960),
            ],
        ])
        assert analyze_tempo_map(mid) == 120.0
