"""Tests for the optimizer module with telemetry and LLM integration."""

import mido
import pytest

from optimizers.auto_tuner import AutoTuner, score_midi, detect_dominant_track_type
from llm.guidance import MockLLMAdvisor


def _make_midi(note_count=20, tpb=480):
    mid = mido.MidiFile(ticks_per_beat=tpb)
    tempo_track = mido.MidiTrack()
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    tempo_track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    tempo_track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(tempo_track)

    data_track = mido.MidiTrack()
    data_track.append(mido.MetaMessage('track_name', name='Guitar', time=0))
    data_track.append(mido.Message('program_change', program=30, channel=0, time=0))
    for i in range(note_count):
        data_track.append(mido.Message('note_on', note=60 + (i % 12), velocity=80, time=100))
        data_track.append(mido.Message('note_off', note=60 + (i % 12), velocity=0, time=240))
    data_track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(data_track)
    return mid


class TestScoring:
    def test_score_returns_tuple(self):
        mid = _make_midi()
        score, metrics = score_midi(mid)
        assert isinstance(score, float)
        assert isinstance(metrics, dict)
        assert 'unique_pitches' in metrics

    def test_empty_midi_score(self):
        mid = mido.MidiFile(ticks_per_beat=480)
        mid.tracks.append(mido.MidiTrack())
        score, metrics = score_midi(mid)
        assert score == 0.0


class TestAutoTunerOptimization:
    def test_optimizer_runs_with_few_trials(self):
        mid = _make_midi()
        tuner = AutoTuner(mid, max_trials=5)
        result = tuner.optimize()
        assert result.best_params is not None
        assert result.best_score != 0
        assert len(result.trials) > 0
        assert len(result.trials) <= 5

    def test_optimizer_returns_config(self):
        mid = _make_midi()
        tuner = AutoTuner(mid, max_trials=3)
        result = tuner.optimize()
        assert 'min_duration_ticks' in result.best_config
        assert 'pitch_cluster' in result.best_config

    def test_optimizer_callback(self):
        mid = _make_midi()
        trials_seen = []
        tuner = AutoTuner(mid, max_trials=3, callback=lambda tr: trials_seen.append(tr))
        tuner.optimize()
        assert len(trials_seen) > 0

    def test_optimizer_with_mock_llm(self):
        mid = _make_midi()
        advisor = MockLLMAdvisor()
        tuner = AutoTuner(mid, max_trials=5, llm_advisor=advisor)
        result = tuner.optimize()
        assert result.best_params is not None
        assert isinstance(result.llm_decisions, list)


class TestTrackTypeDetection:
    def test_detect_guitar(self):
        mid = _make_midi()
        tt = detect_dominant_track_type(mid)
        assert isinstance(tt, str)
        assert tt != ''

    def test_empty_midi(self):
        mid = mido.MidiFile(ticks_per_beat=480)
        mid.tracks.append(mido.MidiTrack())
        tt = detect_dominant_track_type(mid)
        assert tt == 'other'


class TestOptimizerDeterminism:
    def test_same_seed_same_result(self):
        mid = _make_midi()
        t1 = AutoTuner(mid, max_trials=3)
        r1 = t1.optimize()
        t2 = AutoTuner(mid, max_trials=3)
        r2 = t2.optimize()
        assert r1.best_score == r2.best_score
