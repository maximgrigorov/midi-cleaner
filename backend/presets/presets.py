"""Built-in presets for common instrument types and cleaning goals.

Each preset is a dict of config overrides.  Only meaningful keys are set;
anything not listed keeps the current value (global default or user-set).
"""

from __future__ import annotations
from typing import Any

PRESETS: dict[str, dict[str, Any]] = {
    'fx_preserve': {
        'label': 'FX / Preserve',
        'description': 'Keep original FX character — only remove obvious noise.',
        'track_types': ['guitar', 'other'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 60,
            'min_velocity': 3,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 15, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': False,
        },
    },
    'fx_cleaner': {
        'label': 'FX / Cleaner',
        'description': 'Aggressive cleanup for FX tracks — tighter filtering, quantized.',
        'track_types': ['guitar', 'other'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 120,
            'min_velocity': 15,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 30, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': True,
            'quantize': True,
            'quantize_grid': 'eighth',
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': True,
            'cc_numbers': [64, 68],
        },
    },
    'strings_preserve': {
        'label': 'Strings / Preserve',
        'description': 'Keep legato phrasing and polyphony — gentle noise removal only.',
        'track_types': ['strings'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 80,
            'min_velocity': 5,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 10, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': False,
            'remove_overlaps': True,
            'remove_cc': False,
        },
    },
    'strings_cleaner': {
        'label': 'Strings / Cleaner',
        'description': 'Tighter string cleanup — reduce noise, merge voices for cleaner score.',
        'track_types': ['strings'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 120,
            'min_velocity': 12,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 20, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': True,
            'quantize': True,
            'quantize_grid': 'eighth',
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': True,
            'cc_numbers': [64, 68],
        },
    },
    'vocals_preserve': {
        'label': 'Vocals / Preserve',
        'description': 'Keep melody intact — minimal filtering, no quantization.',
        'track_types': ['vocal'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 60,
            'min_velocity': 5,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 10, 'pitch_threshold': 0},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': False,
        },
    },
    'guitar_preserve': {
        'label': 'Guitar / Preserve',
        'description': 'Clean guitar — remove short artifacts, keep note feel.',
        'track_types': ['guitar'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 100,
            'min_velocity': 10,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 20, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': True,
            'cc_numbers': [64, 68],
        },
    },
    'bass_preserve': {
        'label': 'Bass / Preserve',
        'description': 'Bass cleanup — remove ghost notes, keep timing.',
        'track_types': ['bass'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 100,
            'min_velocity': 12,
            'pitch_cluster': {'enabled': True, 'time_window_ticks': 20, 'pitch_threshold': 1},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': True,
            'remove_overlaps': True,
            'remove_cc': True,
            'cc_numbers': [64, 68],
        },
    },
    'drums_preserve': {
        'label': 'Drums / Preserve',
        'description': 'Keep drum hits — very short minimum duration, low velocity floor.',
        'track_types': ['drums'],
        'config': {
            'filter_noise': True,
            'min_duration_ticks': 30,
            'min_velocity': 5,
            'pitch_cluster': {'enabled': False},
            'same_pitch_overlap_resolver': {'enabled': True},
            'remove_triplets': False,
            'quantize': False,
            'merge_voices': False,
            'remove_overlaps': True,
            'remove_cc': False,
        },
    },
}


def get_preset(name: str) -> dict[str, Any] | None:
    return PRESETS.get(name)


def get_preset_config(name: str) -> dict[str, Any]:
    """Return just the config overrides for a preset, or empty dict."""
    preset = PRESETS.get(name)
    return dict(preset['config']) if preset else {}


def list_presets() -> list[dict[str, str]]:
    """Return a list of {id, label, description, track_types} for UI."""
    return [
        {
            'id': k,
            'label': v['label'],
            'description': v['description'],
            'track_types': v['track_types'],
        }
        for k, v in PRESETS.items()
    ]


def suggest_preset(track_type: str) -> str | None:
    """Suggest the best 'preserve' preset for a detected track type."""
    mapping = {
        'guitar': 'fx_preserve',
        'vocal': 'vocals_preserve',
        'strings': 'strings_preserve',
        'bass': 'bass_preserve',
        'drums': 'drums_preserve',
        'other': 'fx_preserve',
    }
    return mapping.get(track_type)


def apply_preset(base_config: dict[str, Any], preset_name: str) -> dict[str, Any]:
    """Overlay preset config onto a base config. Returns a new dict."""
    preset = PRESETS.get(preset_name)
    if not preset:
        return dict(base_config)
    merged = dict(base_config)
    for k, v in preset['config'].items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = {**merged[k], **v}
        else:
            merged[k] = v
    return merged
