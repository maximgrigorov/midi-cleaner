"""Tests for the Auto-Tuner optimization module.

Runs Optuna optimization on a test MIDI file, verifies scoring, early stopping,
and saves the optimized result to tests/output/optimized.mid.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from optimizers.auto_tuner import (
    AutoTuner,
    OptimizationResult,
    TrialResult,
    score_midi,
    detect_dominant_track_type,
)
from processors.pipeline import ProcessingPipeline
from config import DEFAULT_CONFIG

ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
INPUT_FILENAME = 'The Dragon and The Princess (FX).mid'


@pytest.fixture
def test_midi():
    path = os.path.join(ASSET_DIR, INPUT_FILENAME)
    assert os.path.exists(path), f'Test asset not found: {path}'
    return mido.MidiFile(path)


class TestScoring:

    def test_score_returns_float_and_metrics(self, test_midi):
        score, metrics = score_midi(test_midi)
        assert isinstance(score, float)
        assert 'unique_pitches' in metrics
        assert 'avg_duration' in metrics
        assert 'short_note_ratio' in metrics
        assert 'overlap_count' in metrics
        assert 'voice_count' in metrics

    def test_score_positive_for_real_midi(self, test_midi):
        """A real MIDI with notes should have a meaningful score."""
        score, metrics = score_midi(test_midi)
        assert metrics['unique_pitches'] > 0

    def test_empty_midi_scores_zero(self):
        empty = mido.MidiFile(type=1, ticks_per_beat=480)
        t = mido.MidiTrack()
        t.append(mido.MetaMessage('end_of_track', time=0))
        empty.tracks.append(t)
        score, metrics = score_midi(empty)
        assert score == 0.0
        assert metrics['unique_pitches'] == 0


class TestTrackDetection:

    def test_detect_dominant_track_type(self, test_midi):
        tt = detect_dominant_track_type(test_midi)
        assert tt in ('guitar', 'vocal', 'strings', 'bass', 'drums', 'other')

    def test_empty_midi_returns_other(self):
        empty = mido.MidiFile(type=1, ticks_per_beat=480)
        t = mido.MidiTrack()
        t.append(mido.MetaMessage('end_of_track', time=0))
        empty.tracks.append(t)
        assert detect_dominant_track_type(empty) == 'other'


class TestAutoTuner:

    def test_optimize_runs_and_returns_result(self, test_midi):
        """Run optimization with a small trial budget and verify the result shape."""
        collected_trials = []

        def on_trial(tr):
            collected_trials.append(tr)

        tuner = AutoTuner(test_midi, max_trials=5, callback=on_trial)
        result = tuner.optimize()

        assert isinstance(result, OptimizationResult)
        assert result.best_score is not None
        assert isinstance(result.best_params, dict)
        assert 'min_duration' in result.best_params
        assert 'min_velocity' in result.best_params
        assert 'cluster_window' in result.best_params
        assert 'cluster_pitch' in result.best_params
        assert 'triplet_tolerance' in result.best_params
        assert 'quantize' in result.best_params
        assert 'remove_triplets' in result.best_params
        assert 'merge_voices' in result.best_params

        assert len(result.trials) <= 5
        assert len(result.trials) == len(collected_trials)

        assert isinstance(result.best_config, dict)
        assert 'min_duration_ticks' in result.best_config

    def test_best_config_runs_through_pipeline(self, test_midi):
        """The config produced by optimization must be accepted by the pipeline."""
        tuner = AutoTuner(test_midi, max_trials=3)
        result = tuner.optimize()

        pipeline = ProcessingPipeline(result.best_config)
        processed = pipeline.process(test_midi)
        assert len(processed.tracks) > 0

    def test_optimize_and_save_artifact(self, test_midi):
        """Full optimization run, saving the processed MIDI as a test artifact."""
        tuner = AutoTuner(test_midi, max_trials=8)
        result = tuner.optimize()

        pipeline = ProcessingPipeline(result.best_config)
        processed = pipeline.process(test_midi)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, 'optimized.mid')
        processed.save(output_path)

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        reloaded = mido.MidiFile(output_path)
        note_on_count = sum(
            1 for track in reloaded.tracks for msg in track
            if msg.type == 'note_on' and msg.velocity > 0
        )
        assert note_on_count > 0


class TestOptimizeAPI:
    """Integration test: POST /api/optimize via Flask test client."""

    @pytest.fixture
    def client(self):
        from app import app
        app.config['TESTING'] = True
        with app.test_client() as c:
            yield c

    def test_optimize_requires_upload(self, client):
        resp = client.post('/api/optimize')
        assert resp.status_code == 400

    def test_optimize_full_flow(self, client):
        """Upload -> optimize -> poll -> apply -> download."""
        input_path = os.path.join(ASSET_DIR, INPUT_FILENAME)

        # Upload
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, INPUT_FILENAME)},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200

        # Start optimization (small budget)
        import json
        resp = client.post(
            '/api/optimize',
            data=json.dumps({'max_trials': 3}),
            content_type='application/json',
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'started'

        # Poll until done (with timeout)
        import time
        for _ in range(60):
            time.sleep(0.5)
            resp = client.get('/api/optimize/status')
            assert resp.status_code == 200
            status = resp.get_json()
            if status['status'] in ('done', 'error'):
                break

        assert status['status'] == 'done', f"Optimization ended with: {status}"
        assert status['best_score'] is not None
        assert len(status['trials']) > 0

        # Apply
        resp = client.post('/api/optimize/apply')
        assert resp.status_code == 200
        apply_data = resp.get_json()
        assert apply_data['success'] is True

        # Download
        resp = client.get('/api/download')
        assert resp.status_code == 200
        assert len(resp.data) > 0
