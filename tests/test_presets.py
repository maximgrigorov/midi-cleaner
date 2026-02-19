"""Tests for the presets module."""

import copy
import pytest

from presets.presets import (
    PRESETS, list_presets, get_preset, get_preset_config,
    suggest_preset, apply_preset,
)
from config import DEFAULT_CONFIG


class TestPresetListing:
    def test_list_presets_has_required_keys(self):
        presets = list_presets()
        assert len(presets) >= 8
        for p in presets:
            assert 'id' in p
            assert 'label' in p
            assert 'description' in p

    def test_all_preset_ids_unique(self):
        presets = list_presets()
        ids = [p['id'] for p in presets]
        assert len(ids) == len(set(ids))


class TestPresetRetrieval:
    def test_get_known_preset(self):
        p = get_preset('fx_preserve')
        assert p is not None
        assert 'config' in p
        assert 'label' in p

    def test_get_unknown_preset(self):
        assert get_preset('nonexistent') is None

    def test_get_preset_config(self):
        cfg = get_preset_config('fx_preserve')
        assert isinstance(cfg, dict)
        assert 'filter_noise' in cfg

    def test_get_preset_config_unknown(self):
        assert get_preset_config('nope') == {}


class TestPresetSuggestion:
    def test_suggest_guitar(self):
        assert suggest_preset('guitar') is not None

    def test_suggest_vocal(self):
        assert suggest_preset('vocal') == 'vocals_preserve'

    def test_suggest_unknown(self):
        assert suggest_preset('theremin') is None


class TestPresetApplication:
    def test_apply_preset_overrides_config(self):
        base = copy.deepcopy(DEFAULT_CONFIG)
        merged = apply_preset(base, 'fx_cleaner')
        assert merged['min_duration_ticks'] == 120
        assert merged['min_velocity'] == 15

    def test_apply_preset_preserves_unrelated_keys(self):
        base = copy.deepcopy(DEFAULT_CONFIG)
        base['start_bar'] = 5
        merged = apply_preset(base, 'fx_preserve')
        assert merged['start_bar'] == 5

    def test_apply_unknown_preset_returns_copy(self):
        base = copy.deepcopy(DEFAULT_CONFIG)
        merged = apply_preset(base, 'unknown_preset')
        assert merged == base

    def test_apply_preserves_nested_dict(self):
        base = copy.deepcopy(DEFAULT_CONFIG)
        merged = apply_preset(base, 'strings_preserve')
        assert 'pitch_cluster' in merged
        assert isinstance(merged['pitch_cluster'], dict)

    def test_deterministic_output(self):
        base1 = copy.deepcopy(DEFAULT_CONFIG)
        base2 = copy.deepcopy(DEFAULT_CONFIG)
        r1 = apply_preset(base1, 'bass_preserve')
        r2 = apply_preset(base2, 'bass_preserve')
        assert r1 == r2
