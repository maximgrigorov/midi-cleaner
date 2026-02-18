"""Integration tests — verify config flows from DEFAULT_CONFIG through the pipeline.

These tests confirm that:
  - TempoDeduplicator and MergeTracksToSingleTrack are reachable from the pipeline
  - DEFAULT_CONFIG entries are accepted and produce expected behavior
  - Toggling 'enabled' in config actually enables/disables each processor
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import copy
import mido
import pytest

from config import DEFAULT_CONFIG
from processors.pipeline import ProcessingPipeline


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_midi_with_tempo_spam() -> mido.MidiFile:
    """Create a multi-track MIDI file with duplicate tempo events."""
    midi = mido.MidiFile(type=1, ticks_per_beat=480)

    # Conductor track with tempo spam
    conductor = mido.MidiTrack()
    conductor.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=480))
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=480))
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=480))
    conductor.append(mido.MetaMessage('end_of_track', time=0))
    midi.tracks.append(conductor)

    # Data track with a couple of notes
    data = mido.MidiTrack()
    data.append(mido.MetaMessage('track_name', name='Guitar', time=0))
    data.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
    data.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
    data.append(mido.Message('note_on', channel=0, note=62, velocity=80, time=0))
    data.append(mido.Message('note_off', channel=0, note=62, velocity=0, time=480))
    data.append(mido.MetaMessage('end_of_track', time=0))
    midi.tracks.append(data)

    return midi


def _count_set_tempo(midi_file: mido.MidiFile) -> int:
    """Count total set_tempo events across all tracks."""
    count = 0
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                count += 1
    return count


# ── tests ────────────────────────────────────────────────────────────────────

class TestConfigIntegration:

    def test_default_config_has_tempo_deduplicator(self):
        """DEFAULT_CONFIG must include tempo_deduplicator."""
        assert 'tempo_deduplicator' in DEFAULT_CONFIG
        assert DEFAULT_CONFIG['tempo_deduplicator']['enabled'] is True

    def test_default_config_has_merge_tracks(self):
        """DEFAULT_CONFIG must include merge_tracks."""
        assert 'merge_tracks' in DEFAULT_CONFIG
        assert DEFAULT_CONFIG['merge_tracks']['enabled'] is False

    def test_tempo_dedup_runs_in_pipeline(self):
        """With defaults, duplicate set_tempo events should be collapsed."""
        midi = _make_midi_with_tempo_spam()
        assert _count_set_tempo(midi) == 4

        config = copy.deepcopy(DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert _count_set_tempo(result) == 1

    def test_tempo_dedup_disabled_preserves_spam(self):
        """When tempo_deduplicator is disabled, all set_tempo events survive."""
        midi = _make_midi_with_tempo_spam()
        assert _count_set_tempo(midi) == 4

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['tempo_deduplicator'] = {'enabled': False}
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert _count_set_tempo(result) == 4

    def test_merge_tracks_disabled_by_default(self):
        """With defaults, multi-track file stays multi-track."""
        midi = _make_midi_with_tempo_spam()
        config = copy.deepcopy(DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert len(result.tracks) > 1

    def test_merge_tracks_enabled_produces_single_track(self):
        """When merge_tracks is enabled, output must be Type 0 with one track."""
        midi = _make_midi_with_tempo_spam()
        config = copy.deepcopy(DEFAULT_CONFIG)
        config['merge_tracks'] = {'enabled': True, 'include_cc': False, 'cc_whitelist': [64, 68]}
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert result.type == 0
        assert len(result.tracks) == 1
