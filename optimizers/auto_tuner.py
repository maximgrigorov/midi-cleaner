"""Auto-Tuner — Optuna-based parameter optimization for MIDI cleaning.

Wraps the existing ProcessingPipeline (does NOT modify it) and uses Optuna
to search for the parameter combination that maximizes a musical quality score.

Scoring function:
    score = (unique_pitches * 2)
            + avg_duration
            - short_note_ratio * 5
            - overlap_count * 3
            - voice_count * 4

Early stopping rules:
    - improvement < 0.5 % for 4 consecutive iterations
    - 2 consecutive iterations decrease score > 1 %
    - max 40 trials
"""

from __future__ import annotations

import copy
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

import mido
import optuna

from config import DEFAULT_CONFIG
from processors.pipeline import ProcessingPipeline
from telemetry import PipelineContext
from utils.midi_helpers import extract_note_pairs
from utils.track_detector import get_track_info

optuna.logging.set_verbosity(optuna.logging.WARNING)
logger = logging.getLogger(__name__)

# Stagnation threshold for triggering LLM call
_LLM_STALL_ROUNDS = 2

# ── Track-type-aware default parameter ranges ────────────────────────────

TRACK_TYPE_DEFAULTS: dict[str, dict[str, Any]] = {
    'guitar': {
        'min_duration_low': 80, 'min_duration_high': 240,
        'min_velocity_low': 5, 'min_velocity_high': 40,
        'cluster_window_low': 10, 'cluster_window_high': 80,
    },
    'bass': {
        'min_duration_low': 100, 'min_duration_high': 240,
        'min_velocity_low': 10, 'min_velocity_high': 40,
        'cluster_window_low': 15, 'cluster_window_high': 100,
    },
    'vocal': {
        'min_duration_low': 40, 'min_duration_high': 200,
        'min_velocity_low': 0, 'min_velocity_high': 25,
        'cluster_window_low': 10, 'cluster_window_high': 60,
    },
    'drums': {
        'min_duration_low': 40, 'min_duration_high': 120,
        'min_velocity_low': 0, 'min_velocity_high': 15,
        'cluster_window_low': 10, 'cluster_window_high': 40,
    },
    'strings': {
        'min_duration_low': 60, 'min_duration_high': 240,
        'min_velocity_low': 0, 'min_velocity_high': 30,
        'cluster_window_low': 10, 'cluster_window_high': 80,
    },
    'other': {
        'min_duration_low': 40, 'min_duration_high': 240,
        'min_velocity_low': 0, 'min_velocity_high': 40,
        'cluster_window_low': 10, 'cluster_window_high': 120,
    },
}


@dataclass
class TrialResult:
    """Snapshot of a single Optuna trial."""
    number: int
    score: float
    params: dict[str, Any]
    metrics: dict[str, float]


@dataclass
class OptimizationResult:
    """Final result of the optimization run."""
    best_params: dict[str, Any]
    best_score: float
    best_config: dict[str, Any]
    trials: list[TrialResult] = field(default_factory=list)
    stop_reason: str = ''
    llm_decisions: list[dict[str, Any]] = field(default_factory=list)


# ── Scoring ──────────────────────────────────────────────────────────────

def score_midi(midi_file: mido.MidiFile) -> tuple[float, dict[str, float]]:
    """Compute a quality score for a processed MIDI file.

    Returns (score, metrics_dict).
    """
    all_pairs: list[dict[str, Any]] = []
    channels_seen: set[int] = set()

    for idx, track in enumerate(midi_file.tracks):
        pairs = extract_note_pairs(track)
        all_pairs.extend(pairs)
        for p in pairs:
            channels_seen.add(p['channel'])

    if not all_pairs:
        return 0.0, {'unique_pitches': 0, 'avg_duration': 0,
                      'short_note_ratio': 0, 'overlap_count': 0,
                      'voice_count': 0}

    unique_pitches = len({p['pitch'] for p in all_pairs})
    durations = [p['offset'] - p['onset'] for p in all_pairs]
    avg_duration = sum(durations) / len(durations) if durations else 0
    avg_duration_norm = min(avg_duration / 480.0, 10.0)

    short_count = sum(1 for d in durations if d < 60)
    short_note_ratio = short_count / len(all_pairs)

    overlap_count = _count_overlaps(all_pairs)
    voice_count = len(channels_seen)

    score = (
        unique_pitches * 2
        + avg_duration_norm
        - short_note_ratio * 5
        - overlap_count * 3
        - voice_count * 4
    )

    metrics = {
        'unique_pitches': unique_pitches,
        'avg_duration': round(avg_duration, 1),
        'short_note_ratio': round(short_note_ratio, 4),
        'overlap_count': overlap_count,
        'voice_count': voice_count,
    }
    return round(score, 4), metrics


def _count_overlaps(pairs: list[dict[str, Any]]) -> int:
    """Count same-pitch overlapping note pairs within each channel."""
    by_key: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for p in pairs:
        by_key[(p['channel'], p['pitch'])].append(p)

    count = 0
    for notes in by_key.values():
        sorted_notes = sorted(notes, key=lambda n: n['onset'])
        for i in range(1, len(sorted_notes)):
            if sorted_notes[i]['onset'] < sorted_notes[i - 1]['offset']:
                count += 1
    return count


# ── Early-stopping callback ──────────────────────────────────────────────

class _EarlyStopCallback:
    """Optuna callback implementing the two early-stop rules."""

    def __init__(self, stagnation_rounds: int = 4, stagnation_pct: float = 0.5,
                 decline_rounds: int = 2, decline_pct: float = 1.0):
        self._stagnation_rounds = stagnation_rounds
        self._stagnation_pct = stagnation_pct
        self._decline_rounds = decline_rounds
        self._decline_pct = decline_pct
        self._scores: list[float] = []

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        if trial.value is None:
            return
        self._scores.append(trial.value)
        if self._should_stop():
            study.stop()

    def _should_stop(self) -> bool:
        scores = self._scores
        n = len(scores)

        # Rule 1: improvement < stagnation_pct for stagnation_rounds iterations
        if n >= self._stagnation_rounds + 1:
            window = scores[-(self._stagnation_rounds + 1):]
            base = window[0]
            if base != 0:
                all_stagnant = all(
                    abs(s - base) / abs(base) * 100 < self._stagnation_pct
                    for s in window[1:]
                )
                if all_stagnant:
                    return True

        # Rule 2: consecutive decline > decline_pct
        if n >= self._decline_rounds + 1:
            tail = scores[-(self._decline_rounds + 1):]
            declining = True
            for i in range(1, len(tail)):
                if tail[i - 1] == 0 or (tail[i - 1] - tail[i]) / abs(tail[i - 1]) * 100 <= self._decline_pct:
                    declining = False
                    break
            if declining:
                return True

        return False

    @property
    def stop_reason(self) -> str:
        scores = self._scores
        n = len(scores)
        if n >= self._stagnation_rounds + 1:
            window = scores[-(self._stagnation_rounds + 1):]
            base = window[0]
            if base != 0:
                all_stag = all(
                    abs(s - base) / abs(base) * 100 < self._stagnation_pct
                    for s in window[1:]
                )
                if all_stag:
                    return f'stagnation (<{self._stagnation_pct}% for {self._stagnation_rounds} rounds)'
        if n >= self._decline_rounds + 1:
            tail = scores[-(self._decline_rounds + 1):]
            declining = True
            for i in range(1, len(tail)):
                if tail[i - 1] == 0 or (tail[i - 1] - tail[i]) / abs(tail[i - 1]) * 100 <= self._decline_pct:
                    declining = False
                    break
            if declining:
                return f'score declined >{self._decline_pct}% for {self._decline_rounds} consecutive rounds'
        return ''


# ── Detect dominant track type ───────────────────────────────────────────

def detect_dominant_track_type(midi_file: mido.MidiFile) -> str:
    """Return the track type that has the most notes across all data tracks."""
    type_notes: dict[str, int] = defaultdict(int)
    for idx, track in enumerate(midi_file.tracks):
        info = get_track_info(track, idx, midi_file.ticks_per_beat)
        if info['has_notes']:
            type_notes[info['track_type']] += info['note_count']
    if not type_notes:
        return 'other'
    return max(type_notes, key=type_notes.get)


# ── Main optimizer ───────────────────────────────────────────────────────

class AutoTuner:
    """Optuna-based optimizer that wraps the existing ProcessingPipeline."""

    def __init__(self, midi_file: mido.MidiFile, *,
                 max_trials: int = 40,
                 callback: Callable[[TrialResult], None] | None = None,
                 llm_advisor=None):
        self.midi_file = midi_file
        self.max_trials = max_trials
        self._callback = callback
        self._track_type = detect_dominant_track_type(midi_file)
        self._type_hints = TRACK_TYPE_DEFAULTS.get(
            self._track_type, TRACK_TYPE_DEFAULTS['other'])
        self._trials: list[TrialResult] = []
        self._llm = llm_advisor
        self._llm_override: dict[str, Any] | None = None
        self._metrics_before: dict[str, float] = {}

    @property
    def track_type(self) -> str:
        return self._track_type

    def optimize(self) -> OptimizationResult:
        """Run the full Optuna optimization loop. Returns OptimizationResult."""
        _, self._metrics_before = score_midi(self.midi_file)

        early_stop = _EarlyStopCallback()

        study = optuna.create_study(direction='maximize',
                                    sampler=optuna.samplers.TPESampler(seed=42))

        study.optimize(
            self._objective,
            n_trials=self.max_trials,
            callbacks=[early_stop],
            show_progress_bar=False,
        )

        best = study.best_trial
        best_params = best.params
        best_config = self._params_to_config(best_params)

        reason = early_stop.stop_reason or f'max trials ({self.max_trials})'

        result = OptimizationResult(
            best_params=best_params,
            best_score=round(best.value, 4),
            best_config=best_config,
            trials=self._trials,
            stop_reason=reason,
        )
        if self._llm and hasattr(self._llm, 'decisions'):
            result.llm_decisions = list(self._llm.decisions)
        return result

    def _objective(self, trial: optuna.Trial) -> float:
        self._maybe_ask_llm(trial.number)

        params = self._suggest_params(trial)
        config = self._params_to_config(params)

        ctx = PipelineContext(config=config)
        pipeline = ProcessingPipeline(config, context=ctx)
        processed = pipeline.process(self.midi_file)

        score, metrics = score_midi(processed)

        tr = TrialResult(
            number=trial.number,
            score=score,
            params=params,
            metrics=metrics,
        )
        self._trials.append(tr)

        logger.info(
            'Trial %3d | score=%8.4f | pitches=%d avg_dur=%.0f '
            'short=%.3f overlaps=%d voices=%d | %s',
            trial.number, score,
            metrics['unique_pitches'], metrics['avg_duration'],
            metrics['short_note_ratio'], metrics['overlap_count'],
            metrics['voice_count'], params,
        )

        if self._callback:
            self._callback(tr)

        return score

    def _maybe_ask_llm(self, trial_number: int) -> None:
        """Ask LLM for guidance when optimizer stalls."""
        if not self._llm or not self._llm.enabled or self._llm.calls_remaining <= 0:
            return
        if trial_number < _LLM_STALL_ROUNDS:
            return

        recent = self._trials[-_LLM_STALL_ROUNDS:]
        if len(recent) < _LLM_STALL_ROUNDS:
            return
        scores = [t.score for t in recent]
        base = scores[0]
        if base != 0 and all(abs(s - base) / abs(base) * 100 < 0.5 for s in scores[1:]):
            top_issues = self._identify_issues(recent[-1].metrics)
            context = {
                'track_type_guess': self._track_type,
                'metrics_before': self._metrics_before,
                'metrics_after': recent[-1].metrics,
                'last_trial_params': recent[-1].params,
                'last_trial_score': recent[-1].score,
                'top_issues': top_issues,
                'recent_trials': [
                    {'params': t.params, 'score': t.score, 'metrics': t.metrics}
                    for t in self._trials[-3:]
                ],
            }
            suggestion = self._llm.suggest_params(context)
            if suggestion:
                self._llm_override = suggestion
                logger.info('LLM suggested params: %s', suggestion)

    @staticmethod
    def _identify_issues(metrics: dict[str, float]) -> list[str]:
        issues = []
        if metrics.get('short_note_ratio', 0) > 0.1:
            issues.append('short_note_ratio high')
        if metrics.get('overlap_count', 0) > 5:
            issues.append('overlaps high')
        if metrics.get('voice_count', 0) > 2:
            issues.append('polyphony high')
        return issues

    def _suggest_params(self, trial: optuna.Trial) -> dict[str, Any]:
        h = self._type_hints

        if self._llm_override:
            override = self._llm_override
            self._llm_override = None
            return {
                'min_duration': override.get('min_duration', 120),
                'min_velocity': override.get('min_velocity', 10),
                'cluster_window': override.get('cluster_window', 20),
                'cluster_pitch': override.get('cluster_pitch', 1),
                'triplet_tolerance': override.get('triplet_tolerance', 0.15),
                'quantize': override.get('quantize', False),
                'remove_triplets': override.get('remove_triplets', False),
                'merge_voices': override.get('merge_voices', True),
                'same_pitch_resolver': override.get('same_pitch_resolver', True),
            }

        return {
            'min_duration': trial.suggest_int(
                'min_duration', h['min_duration_low'], h['min_duration_high'], step=10),
            'min_velocity': trial.suggest_int(
                'min_velocity', h['min_velocity_low'], h['min_velocity_high']),
            'cluster_window': trial.suggest_int(
                'cluster_window', h['cluster_window_low'], h['cluster_window_high'], step=5),
            'cluster_pitch': trial.suggest_int('cluster_pitch', 0, 2),
            'triplet_tolerance': trial.suggest_float(
                'triplet_tolerance', 0.05, 0.30, step=0.01),
            'quantize': trial.suggest_categorical('quantize', [True, False]),
            'remove_triplets': trial.suggest_categorical('remove_triplets', [True, False]),
            'merge_voices': trial.suggest_categorical('merge_voices', [True, False]),
            'same_pitch_resolver': trial.suggest_categorical('same_pitch_resolver', [True, False]),
        }

    @staticmethod
    def _params_to_config(params: dict[str, Any]) -> dict[str, Any]:
        """Convert flat Optuna params to the nested config the pipeline expects."""
        config = copy.deepcopy(DEFAULT_CONFIG)
        config['min_duration_ticks'] = params['min_duration']
        config['min_velocity'] = params['min_velocity']
        config['pitch_cluster'] = {
            'enabled': True,
            'time_window_ticks': params['cluster_window'],
            'pitch_threshold': params['cluster_pitch'],
        }
        config['triplet_tolerance'] = params['triplet_tolerance']
        config['quantize'] = params['quantize']
        config['remove_triplets'] = params['remove_triplets']
        config['merge_voices'] = params['merge_voices']
        config['filter_noise'] = True
        config['same_pitch_overlap_resolver'] = {
            'enabled': params.get('same_pitch_resolver', True),
        }
        config['tempo_deduplicator'] = {'enabled': True}
        config['remove_overlaps'] = True
        config['remove_cc'] = True
        return config
