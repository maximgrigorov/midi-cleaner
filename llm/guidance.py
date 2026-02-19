"""LLM Guidance module — optional GPT-4o-mini strategy advisor.

The LLM never edits MIDI. It only sees metrics + telemetry summaries and
suggests parameter adjustments. Calls are rate-limited (max 3 per run)
and failures are gracefully ignored.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_PROMPT_PATH = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'llm_strategy_prompt.txt')

# Valid parameter keys the LLM is allowed to suggest
ALLOWED_PARAMS = {
    'min_duration', 'min_velocity', 'cluster_window', 'cluster_pitch',
    'triplet_tolerance', 'quantize', 'remove_triplets', 'merge_voices',
}


def _load_system_prompt() -> str:
    try:
        with open(_PROMPT_PATH) as f:
            return f.read()
    except FileNotFoundError:
        return 'You are a MIDI cleaning strategy advisor. Respond with JSON only.'


class LLMAdvisor:
    """Thin wrapper around an OpenAI-compatible chat endpoint."""

    def __init__(self, *, api_base: str = '', model: str = 'gpt-4o-mini',
                 api_key: str = '', max_calls: int = 3,
                 max_tokens: int = 600, enabled: bool = False):
        self.api_base = api_base or os.environ.get('LLM_API_BASE', 'http://alma:4000')
        self.model = model
        self.api_key = api_key or os.environ.get('LLM_API_KEY', 'sk-placeholder')
        self.max_calls = max_calls
        self.max_tokens = max_tokens
        self.enabled = enabled
        self._calls_made = 0
        self._system_prompt = _load_system_prompt()
        self.decisions: list[dict[str, Any]] = []

    @property
    def calls_remaining(self) -> int:
        return max(0, self.max_calls - self._calls_made)

    def suggest_params(self, context: dict[str, Any]) -> dict[str, Any] | None:
        """Ask LLM for parameter suggestions. Returns param dict or None on failure."""
        if not self.enabled or self._calls_made >= self.max_calls:
            return None

        self._calls_made += 1
        user_msg = json.dumps(context, default=str)
        prompt_tokens_est = len(self._system_prompt.split()) + len(user_msg.split())

        decision_record: dict[str, Any] = {
            'call_number': self._calls_made,
            'prompt_size_tokens_estimate': prompt_tokens_est,
            'response_length': 0,
            'parsed_ok': False,
            'suggested_changes': {},
            'error': None,
        }

        try:
            response_text = self._call_api(user_msg)
            decision_record['response_length'] = len(response_text)
            params = self._parse_response(response_text)
            if params:
                decision_record['parsed_ok'] = True
                decision_record['suggested_changes'] = params
                self.decisions.append(decision_record)
                return params
            else:
                decision_record['error'] = 'empty or invalid params'
        except Exception as e:
            logger.warning('LLM call failed: %s', e)
            decision_record['error'] = str(e)

        self.decisions.append(decision_record)
        return None

    def _call_api(self, user_message: str) -> str:
        """Call the OpenAI-compatible chat API. Override in tests."""
        try:
            import openai
        except ImportError:
            raise RuntimeError('openai package not installed')

        client = openai.OpenAI(base_url=self.api_base, api_key=self.api_key)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {'role': 'system', 'content': self._system_prompt},
                {'role': 'user', 'content': user_message},
            ],
            temperature=0,
            max_tokens=self.max_tokens,
        )
        return resp.choices[0].message.content or ''

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any] | None:
        """Parse LLM response as JSON; return only allowed params."""
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if len(lines) > 2 else lines)
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None
        if not isinstance(data, dict):
            return None
        filtered = {}
        for k, v in data.items():
            if k in ALLOWED_PARAMS:
                filtered[k] = v
        return filtered if filtered else None


class MockLLMAdvisor(LLMAdvisor):
    """Mock advisor for testing — returns a fixed suggestion without network."""

    def __init__(self, fixed_response: dict[str, Any] | None = None, **kwargs):
        super().__init__(**kwargs, enabled=True)
        self._fixed = fixed_response or {
            'min_duration': 100,
            'min_velocity': 8,
            'cluster_window': 25,
            'cluster_pitch': 1,
            'triplet_tolerance': 0.15,
            'quantize': False,
            'remove_triplets': False,
            'merge_voices': True,
        }

    def _call_api(self, user_message: str) -> str:
        return json.dumps(self._fixed)
