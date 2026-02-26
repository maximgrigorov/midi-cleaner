"""Tests for multi-track MIDI (Type 1) support.

Covers upload, per-track processing, track enable/disable, export, and
auto-optimize for multi-track files.
"""

import sys
import os
import copy
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from config import DEFAULT_CONFIG
from processors.pipeline import ProcessingPipeline
from telemetry import PipelineContext, count_notes, count_notes_midi
from optimizers.auto_tuner import (
    AutoTuner,
    detect_dominant_track_type,
    detect_per_track_types,
    score_midi,
)
from utils.track_detector import get_track_info
from app import app

ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')


# ── helpers ─────────────────────────────────────────────────────────────────

def _make_multitrack_midi(num_data_tracks=3, notes_per_track=8) -> mido.MidiFile:
    """Create a multi-track Type 1 MIDI file for testing.

    Returns a file with:
      - Track 0: conductor (tempo + time signature, no notes)
      - Tracks 1..N: data tracks with notes (guitar, bass, vocal names)
    """
    midi = mido.MidiFile(type=1, ticks_per_beat=480)

    # Conductor track
    conductor = mido.MidiTrack()
    conductor.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    conductor.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    conductor.append(mido.MetaMessage('end_of_track', time=0))
    midi.tracks.append(conductor)

    track_names = ['Lead Guitar', 'Bass', 'Vocal', 'Strings', 'Rhythm Guitar',
                   'Drums', 'Synth']
    base_notes = [60, 36, 72, 55, 48, 38, 64]

    for i in range(num_data_tracks):
        track = mido.MidiTrack()
        name = track_names[i % len(track_names)]
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        track.append(mido.Message('program_change', channel=i % 16, program=25 + i, time=0))

        base = base_notes[i % len(base_notes)]
        for j in range(notes_per_track):
            note = base + (j % 12)
            vel = 60 + (j * 5) % 68
            track.append(mido.Message('note_on', channel=i % 16, note=note,
                                       velocity=vel, time=0 if j == 0 else 480))
            track.append(mido.Message('note_off', channel=i % 16, note=note,
                                       velocity=0, time=240))

        track.append(mido.MetaMessage('end_of_track', time=0))
        midi.tracks.append(track)

    return midi


def _count_note_on(midi_file):
    return sum(
        1 for t in midi_file.tracks for m in t
        if m.type == 'note_on' and m.velocity > 0
    )


# ── Pipeline Tests ──────────────────────────────────────────────────────────

class TestMultitrackPipeline:

    def test_multitrack_process_preserves_type1(self):
        """Processing a Type 1 file should produce Type 1 output."""
        midi = _make_multitrack_midi(3)
        config = copy.deepcopy(DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert result.type == 1
        assert len(result.tracks) >= 3  # conductor + data tracks

    def test_conductor_track_not_processed(self):
        """Track 0 (conductor) should be preserved as-is, not run through processors."""
        midi = _make_multitrack_midi(2)
        original_conductor = list(midi.tracks[0])

        config = copy.deepcopy(DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        # Conductor track should retain its meta events
        conductor = result.tracks[0]
        has_tempo = any(m.type == 'set_tempo' for m in conductor)
        has_time_sig = any(m.type == 'time_signature' for m in conductor)
        assert has_tempo
        assert has_time_sig

    def test_each_data_track_processed_independently(self):
        """Each data track should be processed through the full pipeline."""
        midi = _make_multitrack_midi(3, notes_per_track=15)
        config = copy.deepcopy(DEFAULT_CONFIG)
        config['filter_noise'] = True
        config['min_duration_ticks'] = 200  # Will filter some short notes

        ctx = PipelineContext(config=config)
        pipeline = ProcessingPipeline(config, context=ctx)
        result = pipeline.process(midi)

        # Should have processed data tracks
        data_tracks_out = [t for i, t in enumerate(result.tracks) if i > 0]
        assert len(data_tracks_out) > 0

    def test_per_track_overrides(self):
        """Per-track overrides should apply different settings to different tracks."""
        midi = _make_multitrack_midi(2, notes_per_track=10)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['filter_noise'] = True
        config['min_duration_ticks'] = 50
        config['min_velocity'] = 5
        config['track_overrides'] = {
            '1': {'min_duration_ticks': 50, 'min_velocity': 5},
            '2': {'min_duration_ticks': 500, 'min_velocity': 100},
        }

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        # Track 2 should have fewer notes due to aggressive filtering
        track1_notes = count_notes(result.tracks[1])
        track2_notes = count_notes(result.tracks[2])
        assert track1_notes > track2_notes

    def test_disabled_tracks_excluded(self):
        """Disabled tracks should be excluded from output entirely."""
        midi = _make_multitrack_midi(3, notes_per_track=5)
        assert len(midi.tracks) == 4  # conductor + 3 data

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [2]  # Disable the second data track

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        # Output should have 3 tracks: conductor + 2 remaining data tracks
        assert len(result.tracks) == 3

    def test_disabled_all_data_tracks(self):
        """Disabling all data tracks should produce conductor-only output."""
        midi = _make_multitrack_midi(2)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [1, 2]

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert len(result.tracks) == 1  # Only conductor
        assert count_notes_midi(result) == 0

    def test_conductor_cannot_be_disabled(self):
        """Track 0 (conductor) should always be included even if in disabled_tracks."""
        midi = _make_multitrack_midi(2)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [0, 1]  # Try to disable conductor

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        # Conductor (track 0) should still be present
        assert len(result.tracks) >= 1
        has_tempo = any(m.type == 'set_tempo' for m in result.tracks[0])
        assert has_tempo

    def test_track_order_preserved(self):
        """Output tracks should maintain original order."""
        midi = _make_multitrack_midi(3)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [2]

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        # Track names should be in original order (minus disabled)
        names = []
        for t in result.tracks:
            for m in t:
                if m.type == 'track_name':
                    names.append(m.name)
                    break
        # Track 1 = Lead Guitar, Track 3 = Vocal (track 2 = Bass was disabled)
        assert 'Lead Guitar' in names
        assert 'Vocal' in names
        assert 'Bass' not in names

    def test_single_enabled_track_stays_type1(self):
        """If only one data track enabled, output should still be Type 1."""
        midi = _make_multitrack_midi(3)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [2, 3]
        config['merge_tracks'] = {'enabled': False, 'include_cc': False, 'cc_whitelist': []}

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert result.type == 1

    def test_merge_tracks_overrides_type1(self):
        """Explicit merge_tracks should flatten to Type 0 even for multi-track input."""
        midi = _make_multitrack_midi(3)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['merge_tracks'] = {'enabled': True, 'include_cc': False, 'cc_whitelist': []}

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert result.type == 0
        assert len(result.tracks) == 1


# ── Type 0 (single-track) Backward Compatibility ───────────────────────────

class TestSingleTrackBackwardCompat:

    def test_type0_still_works(self):
        """A Type 0 single-track MIDI should process normally."""
        midi = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.Message('note_on', channel=0, note=62, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=62, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))
        midi.tracks.append(track)

        config = copy.deepcopy(DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert result.type == 0
        assert _count_note_on(result) > 0

    def test_disabled_tracks_ignored_for_type0(self):
        """disabled_tracks should be harmless for Type 0 files."""
        midi = mido.MidiFile(type=0, ticks_per_beat=480)
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
        track.append(mido.Message('note_on', channel=0, note=60, velocity=80, time=0))
        track.append(mido.Message('note_off', channel=0, note=60, velocity=0, time=480))
        track.append(mido.MetaMessage('end_of_track', time=0))
        midi.tracks.append(track)

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['disabled_tracks'] = [5, 6]  # Non-existent tracks

        pipeline = ProcessingPipeline(config)
        result = pipeline.process(midi)

        assert _count_note_on(result) > 0


# ── Auto Optimize Multitrack Tests ──────────────────────────────────────────

class TestAutoOptimizeMultitrack:

    def test_per_track_optimization(self):
        """Multi-track files should optimize each track independently."""
        midi = _make_multitrack_midi(2, notes_per_track=6)
        tuner = AutoTuner(midi, max_trials=6)
        result = tuner.optimize()

        # Multi-track should return track_overrides
        assert 'track_overrides' in result.best_params
        assert 'per_track_types' in result.best_params

        overrides = result.best_params['track_overrides']
        assert len(overrides) == 2  # 2 data tracks

    def test_per_track_types_detected(self):
        """Each track should get its own detected type."""
        midi = _make_multitrack_midi(3)
        types = detect_per_track_types(midi)

        assert len(types) == 3  # 3 data tracks
        assert 1 in types
        assert 2 in types
        assert 3 in types
        for track_type in types.values():
            assert track_type in ('guitar', 'bass', 'vocal', 'strings', 'drums', 'other')

    def test_best_config_has_track_overrides(self):
        """Optimized config for multi-track should include track_overrides."""
        midi = _make_multitrack_midi(2)
        tuner = AutoTuner(midi, max_trials=6)
        result = tuner.optimize()

        assert 'track_overrides' in result.best_config
        overrides = result.best_config['track_overrides']
        for key, params in overrides.items():
            assert 'min_duration_ticks' in params
            assert 'min_velocity' in params

    def test_best_config_runs_through_pipeline(self):
        """Optimized config should be accepted by ProcessingPipeline."""
        midi = _make_multitrack_midi(2, notes_per_track=6)
        tuner = AutoTuner(midi, max_trials=4)
        result = tuner.optimize()

        pipeline = ProcessingPipeline(result.best_config)
        processed = pipeline.process(midi)
        assert len(processed.tracks) > 0


# ── API Integration Tests ──────────────────────────────────────────────────

class TestMultitrackAPI:

    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as c:
            yield c

    def test_upload_multitrack(self, client):
        """Upload a multi-track MIDI file and verify response."""
        input_path = os.path.join(ASSET_DIR, 'The Dragon and The Princess (FX).mid')
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, 'test_multitrack.mid')},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['type'] == 1
        assert data['num_tracks'] >= 2
        assert len(data['tracks']) >= 2

    def test_process_multitrack(self, client):
        """Upload + process a multi-track file."""
        input_path = os.path.join(ASSET_DIR, 'The Dragon and The Princess (FX).mid')
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, 'test_multitrack.mid')},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200

        config = copy.deepcopy(DEFAULT_CONFIG)
        resp = client.post(
            '/api/process',
            data=json.dumps(config),
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True

    def test_process_multitrack_with_disabled_tracks(self, client):
        """Process multi-track with some tracks disabled."""
        input_path = os.path.join(ASSET_DIR, 'The Dragon and The Princess (FX).mid')
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, 'test_multitrack.mid')},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200
        upload = resp.get_json()
        note_tracks = [t for t in upload['tracks'] if t['has_notes']]

        # Disable the last note track
        if len(note_tracks) > 1:
            last_idx = note_tracks[-1]['index']
            config = copy.deepcopy(DEFAULT_CONFIG)
            config['disabled_tracks'] = [last_idx]
            resp = client.post(
                '/api/process',
                data=json.dumps(config),
                content_type='application/json',
            )
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True

            # Output should have fewer tracks than input
            output_tracks = data['tracks']
            assert len(output_tracks) < len(upload['tracks'])

    def test_download_multitrack(self, client):
        """Upload, process, download a multi-track file and verify Type 1 output."""
        input_path = os.path.join(ASSET_DIR, 'The Dragon and The Princess (FX).mid')
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, 'test_multitrack.mid')},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200

        config = copy.deepcopy(DEFAULT_CONFIG)
        resp = client.post(
            '/api/process',
            data=json.dumps(config),
            content_type='application/json',
        )
        assert resp.status_code == 200

        resp = client.get('/api/download')
        assert resp.status_code == 200
        assert len(resp.data) > 0

        # Verify the downloaded file is valid Type 1 MIDI
        import io
        output_midi = mido.MidiFile(file=io.BytesIO(resp.data))
        assert output_midi.type == 1
        assert _count_note_on(output_midi) > 0

    def test_process_with_per_track_overrides(self, client):
        """Process with per-track parameter overrides."""
        input_path = os.path.join(ASSET_DIR, 'The Dragon and The Princess (FX).mid')
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, 'test_multitrack.mid')},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['track_overrides'] = {
            '1': {'min_duration_ticks': 50, 'min_velocity': 5},
            '2': {'min_duration_ticks': 200, 'min_velocity': 50},
        }
        resp = client.post(
            '/api/process',
            data=json.dumps(config),
            content_type='application/json',
        )
        assert resp.status_code == 200
        assert resp.get_json()['success'] is True
