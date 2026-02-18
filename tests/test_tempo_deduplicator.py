"""Unit tests for TempoDeduplicator.

Covers:
  - Duplicate set_tempo events are collapsed to one
  - Real tempo changes (different BPM) are preserved
  - Disabled processor returns the track unchanged
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from processors.tempo_deduplicator import TempoDeduplicator
from utils.midi_helpers import to_absolute_time


# ── helpers ─────────────────────────────────────────────────────────────────

ENABLED_CFG = {'tempo_deduplicator': {'enabled': True}}
DISABLED_CFG = {'tempo_deduplicator': {'enabled': False}}

# 120 BPM = 500000 µs/beat,  100 BPM = 600000 µs/beat
TEMPO_120 = 500000
TEMPO_100 = 600000


def _tempo_events(track) -> list[tuple[int, int]]:
    """Extract (abs_tick, tempo_value) for every set_tempo in the track."""
    result = []
    abs_time = 0
    for msg in track:
        abs_time += msg.time
        if msg.type == 'set_tempo':
            result.append((abs_time, msg.tempo))
    return result


# ── tests ────────────────────────────────────────────────────────────────────

class TestTempoDeduplicator:

    def test_duplicate_tempos_collapsed(self):
        """Three identical set_tempo events should collapse to one."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(ENABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        tempos = _tempo_events(result)
        assert len(tempos) == 1, f"Expected 1 set_tempo, got {len(tempos)}"
        assert tempos[0][1] == TEMPO_120

    def test_same_tick_duplicates_collapsed(self):
        """Multiple identical set_tempo at the same tick → keep one."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(ENABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        tempos = _tempo_events(result)
        assert len(tempos) == 1

    def test_real_tempo_changes_preserved(self):
        """Tempo 120 → 100 → 120 must keep all three distinct values."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_100, time=480))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(ENABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        tempos = _tempo_events(result)
        assert len(tempos) == 3
        assert tempos[0][1] == TEMPO_120
        assert tempos[1][1] == TEMPO_100
        assert tempos[2][1] == TEMPO_120

    def test_timing_preserved_after_removal(self):
        """Events after a removed set_tempo must keep their original tick."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        # Duplicate at tick 480 — will be removed
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480))
        # A note_on at tick 960 must remain at tick 960
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=480))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(ENABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        abs_msgs = to_absolute_time(result)
        note_ons = [(t, m) for t, m in abs_msgs if m.type == 'note_on']
        assert note_ons[0][0] == 960, "Note timing must not shift"

    def test_disabled_returns_identical_track(self):
        """When disabled the processor returns the exact same track object."""
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=TEMPO_120, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(DISABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        assert result is track

    def test_no_tempo_events_passthrough(self):
        """A track with no set_tempo should pass through unchanged."""
        track = mido.MidiTrack()
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        proc = TempoDeduplicator(ENABLED_CFG)
        result = proc.process(track, ticks_per_beat=480)

        tempos = _tempo_events(result)
        assert len(tempos) == 0
