"""Telemetry models for pipeline processing instrumentation.

Provides ProcessorTelemetry (per-step stats), PipelineReport (full run
summary), and PipelineContext (runtime bag passed through the pipeline).
All models are JSON-serializable via .to_dict().
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


PIPELINE_VERSION = '2.0.0'


@dataclass
class ProcessorTelemetry:
    """Stats collected for a single processor step."""

    name: str = ''
    enabled: bool = True
    started_at: float = 0.0
    ended_at: float = 0.0
    duration_ms: int = 0
    input_note_count: int = 0
    output_note_count: int = 0
    notes_removed: int = 0
    overlaps_resolved: int = 0
    clusters_merged: int = 0
    tempo_events_removed: int = 0
    tracks_merged: bool = False
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'enabled': self.enabled,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'duration_ms': self.duration_ms,
            'input_note_count': self.input_note_count,
            'output_note_count': self.output_note_count,
            'notes_removed': self.notes_removed,
            'overlaps_resolved': self.overlaps_resolved,
            'clusters_merged': self.clusters_merged,
            'tempo_events_removed': self.tempo_events_removed,
            'tracks_merged': self.tracks_merged,
            'warnings': self.warnings,
            'extra': self.extra,
        }


@dataclass
class PipelineReport:
    """Full report for a single pipeline run."""

    pipeline_version: str = PIPELINE_VERSION
    file_name: str = ''
    track_names: list[str] = field(default_factory=list)
    input_metrics: dict[str, Any] = field(default_factory=dict)
    output_metrics: dict[str, Any] = field(default_factory=dict)
    steps: list[ProcessorTelemetry] = field(default_factory=list)
    total_duration_ms: int = 0
    config_used: dict[str, Any] = field(default_factory=dict)
    preset_applied: str = ''
    best_params: dict[str, Any] = field(default_factory=dict)
    optimizer_history: list[dict[str, Any]] = field(default_factory=list)
    llm_decisions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'pipeline_version': self.pipeline_version,
            'file_name': self.file_name,
            'track_names': self.track_names,
            'input_metrics': self.input_metrics,
            'output_metrics': self.output_metrics,
            'steps': [s.to_dict() for s in self.steps],
            'total_duration_ms': self.total_duration_ms,
            'config_used': self.config_used,
            'preset_applied': self.preset_applied,
            'best_params': self.best_params,
            'optimizer_history': self.optimizer_history,
            'llm_decisions': self.llm_decisions,
        }


class PipelineContext:
    """Runtime context passed through the pipeline.

    Holds the report, config snapshot, and a logger-like interface.
    Backwards-compatible: pipeline creates one automatically if not provided.
    """

    def __init__(self, file_name: str = '', config: dict[str, Any] | None = None):
        self.report = PipelineReport(file_name=file_name)
        if config:
            self.report.config_used = _safe_config(config)
        self._current_step: ProcessorTelemetry | None = None

    def begin_step(self, name: str, enabled: bool, input_note_count: int) -> ProcessorTelemetry:
        step = ProcessorTelemetry(
            name=name,
            enabled=enabled,
            input_note_count=input_note_count,
            started_at=time.time(),
        )
        self._current_step = step
        return step

    def end_step(self, output_note_count: int) -> None:
        step = self._current_step
        if step is None:
            return
        step.ended_at = time.time()
        step.duration_ms = int((step.ended_at - step.started_at) * 1000)
        step.output_note_count = output_note_count
        step.notes_removed = max(0, step.input_note_count - output_note_count)
        self.report.steps.append(step)
        self._current_step = None

    def skip_step(self, name: str, input_note_count: int) -> None:
        """Record a disabled/skipped processor step."""
        step = ProcessorTelemetry(
            name=name,
            enabled=False,
            input_note_count=input_note_count,
            output_note_count=input_note_count,
        )
        self.report.steps.append(step)

    def add_warning(self, msg: str) -> None:
        if self._current_step:
            self._current_step.warnings.append(msg)

    def finalize(self, total_start: float) -> PipelineReport:
        self.report.total_duration_ms = int((time.time() - total_start) * 1000)
        return self.report


def count_notes(track) -> int:
    """Count note_on events with velocity > 0 in a mido track."""
    return sum(1 for m in track if m.type == 'note_on' and m.velocity > 0)


def count_notes_midi(midi_file) -> int:
    """Count total note_on events across all tracks."""
    return sum(count_notes(t) for t in midi_file.tracks)


def _safe_config(config: dict) -> dict:
    """Return a JSON-safe shallow copy of the config."""
    safe = {}
    for k, v in config.items():
        if isinstance(v, (str, int, float, bool, type(None))):
            safe[k] = v
        elif isinstance(v, dict):
            safe[k] = _safe_config(v)
        elif isinstance(v, (list, tuple)):
            safe[k] = list(v)
        else:
            safe[k] = str(v)
    return safe
