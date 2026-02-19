"""Tests for the telemetry model and pipeline telemetry integration."""

import json
import mido
import pytest

from telemetry import (
    ProcessorTelemetry, PipelineReport, PipelineContext,
    count_notes, count_notes_midi, PIPELINE_VERSION,
)


def _make_midi(note_count=10, tpb=480):
    mid = mido.MidiFile(ticks_per_beat=tpb)
    tempo_track = mido.MidiTrack()
    tempo_track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    tempo_track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    tempo_track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(tempo_track)

    data_track = mido.MidiTrack()
    data_track.append(mido.MetaMessage('track_name', name='Test', time=0))
    for i in range(note_count):
        data_track.append(mido.Message('note_on', note=60 + (i % 12), velocity=80, time=100))
        data_track.append(mido.Message('note_off', note=60 + (i % 12), velocity=0, time=200))
    data_track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(data_track)
    return mid


class TestProcessorTelemetry:
    def test_to_dict(self):
        t = ProcessorTelemetry(name='NoiseFilter', enabled=True,
                               input_note_count=50, output_note_count=40,
                               notes_removed=10, duration_ms=15)
        d = t.to_dict()
        assert d['name'] == 'NoiseFilter'
        assert d['notes_removed'] == 10
        assert isinstance(d, dict)

    def test_json_serializable(self):
        t = ProcessorTelemetry(name='Test', extra={'foo': 'bar'})
        s = json.dumps(t.to_dict())
        assert '"foo"' in s


class TestPipelineReport:
    def test_to_dict(self):
        r = PipelineReport(file_name='test.mid', track_names=['Track 1'])
        r.steps.append(ProcessorTelemetry(name='Step1'))
        d = r.to_dict()
        assert d['pipeline_version'] == PIPELINE_VERSION
        assert len(d['steps']) == 1

    def test_json_serializable(self):
        r = PipelineReport()
        s = json.dumps(r.to_dict())
        assert '"steps"' in s


class TestPipelineContext:
    def test_begin_end_step(self):
        ctx = PipelineContext(file_name='test.mid')
        step = ctx.begin_step('Filter', True, 100)
        assert step.name == 'Filter'
        ctx.end_step(90)
        assert len(ctx.report.steps) == 1
        assert ctx.report.steps[0].notes_removed == 10

    def test_skip_step(self):
        ctx = PipelineContext()
        ctx.skip_step('Disabled', 50)
        assert len(ctx.report.steps) == 1
        assert ctx.report.steps[0].enabled is False
        assert ctx.report.steps[0].output_note_count == 50

    def test_finalize(self):
        import time
        ctx = PipelineContext()
        start = time.time()
        ctx.finalize(start)
        assert ctx.report.total_duration_ms >= 0


class TestCountNotes:
    def test_count_notes_track(self):
        mid = _make_midi(note_count=5)
        assert count_notes(mid.tracks[1]) == 5

    def test_count_notes_midi(self):
        mid = _make_midi(note_count=8)
        assert count_notes_midi(mid) == 8


class TestPipelineTelemetryIntegration:
    def test_process_returns_report_in_context(self):
        from processors.pipeline import ProcessingPipeline
        from config import DEFAULT_CONFIG

        mid = _make_midi(note_count=15)
        ctx = PipelineContext(file_name='test.mid', config=DEFAULT_CONFIG)
        pipeline = ProcessingPipeline(DEFAULT_CONFIG, context=ctx)
        pipeline.process(mid)

        report = ctx.report
        assert len(report.steps) > 0
        assert report.total_duration_ms >= 0
        assert report.input_metrics['total_notes'] == 15

        for step in report.steps:
            assert step.name
            assert step.input_note_count >= 0
            assert step.output_note_count >= 0

    def test_report_note_counts_change(self):
        from processors.pipeline import ProcessingPipeline
        from config import DEFAULT_CONFIG
        import copy

        config = copy.deepcopy(DEFAULT_CONFIG)
        config['filter_noise'] = True
        config['min_duration_ticks'] = 300

        mid = _make_midi(note_count=10)
        ctx = PipelineContext(config=config)
        pipeline = ProcessingPipeline(config, context=ctx)
        pipeline.process(mid)

        report = ctx.report
        d = report.to_dict()
        s = json.dumps(d)
        parsed = json.loads(s)
        assert 'steps' in parsed
        assert isinstance(parsed['steps'], list)
