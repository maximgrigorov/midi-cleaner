"""Tests for the LLM guidance module (mocked — no network required)."""

import json
import pytest

from llm.guidance import LLMAdvisor, MockLLMAdvisor, ALLOWED_PARAMS


class TestMockLLMAdvisor:
    def test_suggest_returns_dict(self):
        advisor = MockLLMAdvisor()
        result = advisor.suggest_params({'track_type_guess': 'guitar'})
        assert isinstance(result, dict)
        assert all(k in ALLOWED_PARAMS for k in result)

    def test_call_count_limit(self):
        advisor = MockLLMAdvisor(max_calls=2)
        assert advisor.calls_remaining == 2
        advisor.suggest_params({})
        assert advisor.calls_remaining == 1
        advisor.suggest_params({})
        assert advisor.calls_remaining == 0
        result = advisor.suggest_params({})
        assert result is None

    def test_decisions_recorded(self):
        advisor = MockLLMAdvisor()
        advisor.suggest_params({'some': 'context'})
        assert len(advisor.decisions) == 1
        d = advisor.decisions[0]
        assert d['call_number'] == 1
        assert d['parsed_ok'] is True
        assert isinstance(d['suggested_changes'], dict)

    def test_custom_fixed_response(self):
        advisor = MockLLMAdvisor(fixed_response={'min_duration': 200, 'quantize': True})
        result = advisor.suggest_params({})
        assert result['min_duration'] == 200
        assert result['quantize'] is True


class TestLLMAdvisorParsing:
    def test_parse_valid_json(self):
        text = '{"min_duration": 120, "min_velocity": 10}'
        result = LLMAdvisor._parse_response(text)
        assert result == {'min_duration': 120, 'min_velocity': 10}

    def test_parse_json_with_code_fence(self):
        text = '```json\n{"quantize": true}\n```'
        result = LLMAdvisor._parse_response(text)
        assert result == {'quantize': True}

    def test_parse_invalid_json(self):
        result = LLMAdvisor._parse_response('not json at all')
        assert result is None

    def test_parse_filters_unknown_keys(self):
        text = '{"min_duration": 100, "unknown_key": 42}'
        result = LLMAdvisor._parse_response(text)
        assert 'unknown_key' not in result
        assert result['min_duration'] == 100

    def test_parse_empty_string(self):
        result = LLMAdvisor._parse_response('')
        assert result is None

    def test_parse_array_rejected(self):
        result = LLMAdvisor._parse_response('[1, 2, 3]')
        assert result is None


class TestLLMAdvisorDisabled:
    def test_disabled_returns_none(self):
        advisor = LLMAdvisor(enabled=False)
        result = advisor.suggest_params({'test': True})
        assert result is None
        assert len(advisor.decisions) == 0
