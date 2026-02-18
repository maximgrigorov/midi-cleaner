"""Unit tests for MergeTracksToSingleTrack.

Covers:
  - Multi-track → single-track conversion
  - Note count and timing preserved
  - Meta events preserved
  - Correct ordering at same tick (note_off before note_on)
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from processors.merge_tracks_to_single import MergeTracksToSingleTrack
from utils.midi_helpers import to_absolute_time, extract_note_pairs


# ── helpers ─────────────────────────────────────────────────────────────────

ENABLED_CFG = {'merge_tracks': {'enabled': True, 'include_cc': False}}
DISABLED_CFG = {'merge_tracks': {'enabled': False}}
CC_CFG = {'merge_tracks': {'enabled': True, 'include_cc': True, 'cc_whitelist': [64]}}
CC_ALL_CFG = {'merge_tracks': {'enabled': True, 'include_cc': True, 'cc_whitelist': []}}


def _make_midi(*tracks: mido.MidiTrack, tpb: int = 480) -> mido.MidiFile:
    """Build a MidiFile from one or more pre-built tracks."""
    midi = mido.MidiFile(type=1, ticks_per_beat=tpb)
    for t in tracks:
        midi.tracks.append(t)
    return midi


def _conductor_track() -> mido.MidiTrack:
    """Minimal conductor track: tempo + time sig."""
    t = mido.MidiTrack()
    t.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    t.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    t.append(mido.MetaMessage('end_of_track', time=0))
    return t


def _note_track(channel: int, notes: list[tuple[int, int, int, int]]) -> mido.MidiTrack:
    """Build a track from a list of (pitch, onset, offset, velocity) tuples.

    Onset/offset are absolute ticks; the helper converts to delta times.
    """
    events: list[tuple[int, mido.Message]] = []
    for pitch, onset, offset, velocity in notes:
        events.append((onset, mido.Message(
            'note_on', channel=channel, note=pitch, velocity=velocity, time=0)))
        events.append((offset, mido.Message(
            'note_off', channel=channel, note=pitch, velocity=0, time=0)))

    events.sort(key=lambda e: (e[0], 0 if e[1].type == 'note_off' else 1))

    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=f'Ch{channel}', time=0))
    prev = 0
    for abs_t, msg in events:
        track.append(msg.copy(time=abs_t - prev))
        prev = abs_t
    track.append(mido.MetaMessage('end_of_track', time=0))
    return track


# ── tests ────────────────────────────────────────────────────────────────────

class TestMergeTracksToSingleTrack:

    def test_multi_track_becomes_single(self):
        """A 3-track MIDI file must become a Type 0 file with 1 track."""
        midi = _make_midi(
            _conductor_track(),
            _note_track(0, [(60, 0, 480, 80)]),
            _note_track(1, [(64, 0, 480, 80)]),
        )
        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        assert result.type == 0
        assert len(result.tracks) == 1

    def test_note_count_preserved(self):
        """All notes from all tracks must appear in the merged output."""
        track_a = _note_track(0, [(60, 0, 480, 80), (62, 480, 960, 80)])
        track_b = _note_track(1, [(64, 0, 480, 70)])
        midi = _make_midi(_conductor_track(), track_a, track_b)

        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        pairs = extract_note_pairs(result.tracks[0])
        assert len(pairs) == 3, f"Expected 3 notes, got {len(pairs)}"

    def test_note_timing_unchanged(self):
        """Onset and offset ticks must be identical after merging."""
        original_notes = [(60, 0, 480, 80), (62, 960, 1440, 90)]
        midi = _make_midi(_conductor_track(), _note_track(0, original_notes))

        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        pairs = extract_note_pairs(result.tracks[0])
        pairs.sort(key=lambda n: n['onset'])

        assert pairs[0]['onset'] == 0
        assert pairs[0]['offset'] == 480
        assert pairs[1]['onset'] == 960
        assert pairs[1]['offset'] == 1440

    def test_meta_events_preserved(self):
        """Tempo and time signature from conductor track must survive merge."""
        midi = _make_midi(
            _conductor_track(),
            _note_track(0, [(60, 0, 480, 80)]),
        )
        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        merged = result.tracks[0]
        meta_types = {msg.type for msg in merged if msg.is_meta}
        assert 'set_tempo' in meta_types
        assert 'time_signature' in meta_types

    def test_note_off_before_note_on_at_same_tick(self):
        """At the same tick, note_off must precede note_on (prevents stuck notes)."""
        # Note A ends at tick 480, Note B starts at tick 480
        track = _note_track(0, [(60, 0, 480, 80), (62, 480, 960, 80)])
        midi = _make_midi(_conductor_track(), track)

        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        abs_msgs = to_absolute_time(result.tracks[0])
        # Collect events exactly at tick 480
        at_480 = [msg for t, msg in abs_msgs if t == 480]

        note_off_idx = None
        note_on_idx = None
        for i, msg in enumerate(at_480):
            if msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if note_off_idx is None:
                    note_off_idx = i
            elif msg.type == 'note_on' and msg.velocity > 0:
                if note_on_idx is None:
                    note_on_idx = i

        assert note_off_idx is not None and note_on_idx is not None
        assert note_off_idx < note_on_idx, "note_off must come before note_on at same tick"

    def test_channels_preserved(self):
        """Notes from different channels must keep their original channel."""
        midi = _make_midi(
            _conductor_track(),
            _note_track(0, [(60, 0, 480, 80)]),
            _note_track(5, [(64, 0, 480, 70)]),
        )
        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        pairs = extract_note_pairs(result.tracks[0])
        channels = {p['channel'] for p in pairs}
        assert channels == {0, 5}

    def test_cc_excluded_by_default(self):
        """CC events should not appear when include_cc is False."""
        track = mido.MidiTrack()
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message('control_change', channel=0, control=64, value=127, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        midi = _make_midi(_conductor_track(), track)
        proc = MergeTracksToSingleTrack(ENABLED_CFG)
        result = proc.process(midi)

        cc_msgs = [m for m in result.tracks[0] if m.type == 'control_change']
        assert len(cc_msgs) == 0

    def test_cc_whitelist_included(self):
        """Whitelisted CC events should appear when include_cc is True."""
        track = mido.MidiTrack()
        track.append(mido.Message('control_change', channel=0, control=64, value=127, time=0))
        track.append(mido.Message('control_change', channel=0, control=11, value=100, time=0))
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))

        midi = _make_midi(_conductor_track(), track)
        # Whitelist only CC#64
        proc = MergeTracksToSingleTrack(CC_CFG)
        result = proc.process(midi)

        cc_msgs = [m for m in result.tracks[0] if m.type == 'control_change']
        assert len(cc_msgs) == 1
        assert cc_msgs[0].control == 64

    def test_disabled_returns_original(self):
        """When disabled the processor must return the original MidiFile object."""
        midi = _make_midi(
            _conductor_track(),
            _note_track(0, [(60, 0, 480, 80)]),
        )
        proc = MergeTracksToSingleTrack(DISABLED_CFG)
        result = proc.process(midi)

        assert result is midi
