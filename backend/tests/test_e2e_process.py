"""End-to-end test — upload a MIDI file, process with recommended settings, download result.

Runs the full Flask request pipeline via the test client (no external services,
no GUI, headless-safe).  The processed MIDI is saved as a test artifact at:
    tests/output/The Dragon and The Princess (FX)_processed_by_tests.mid
"""

import sys
import os
import io
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mido
import pytest

from app import app

ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
INPUT_FILENAME = 'The Dragon and The Princess (FX).mid'
OUTPUT_FILENAME = 'The Dragon and The Princess (FX)_processed_by_tests.mid'

RECOMMENDED_CONFIG = {
    'tempo_deduplicator': {'enabled': True},
    'merge_voices': True,
    'remove_overlaps': True,
    'remove_triplets': False,
    'quantize': False,
    'remove_cc': False,
    'filter_noise': True,
    'min_duration_ticks': 80,
    'min_velocity': 3,
    'pitch_cluster': {
        'enabled': True,
        'time_window_ticks': 20,
        'pitch_threshold': 1,
    },
    'same_pitch_overlap_resolver': {'enabled': True},
    'merge_tracks': {
        'enabled': True,
        'include_cc': False,
        'cc_whitelist': [],
    },
}


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _count_note_on(midi_file):
    """Count note_on events with velocity > 0 across all tracks."""
    return sum(
        1
        for track in midi_file.tracks
        for msg in track
        if msg.type == 'note_on' and msg.velocity > 0
    )


def _count_set_tempo(midi_file):
    return sum(
        1
        for track in midi_file.tracks
        for msg in track
        if msg.type == 'set_tempo'
    )


class TestEndToEnd:

    def test_process_and_download(self, client):
        input_path = os.path.join(ASSET_DIR, INPUT_FILENAME)
        assert os.path.exists(input_path), f'Test asset not found: {input_path}'

        input_midi = mido.MidiFile(input_path)
        input_note_on_count = _count_note_on(input_midi)
        assert input_note_on_count > 0, 'Input MIDI has no notes'

        # 1. Upload
        with open(input_path, 'rb') as f:
            resp = client.post(
                '/api/upload',
                data={'file': (f, INPUT_FILENAME)},
                content_type='multipart/form-data',
            )
        assert resp.status_code == 200, f'Upload failed: {resp.get_json()}'
        upload_data = resp.get_json()
        assert upload_data.get('num_tracks', 0) > 0

        # 2. Process with recommended settings
        resp = client.post(
            '/api/process',
            data=json.dumps(RECOMMENDED_CONFIG),
            content_type='application/json',
        )
        assert resp.status_code == 200, f'Process failed: {resp.get_json()}'
        process_data = resp.get_json()
        assert process_data.get('success') is True

        # 3. Download processed MIDI
        resp = client.get('/api/download')
        assert resp.status_code == 200, 'Download failed'
        assert len(resp.data) > 0, 'Downloaded file is empty'

        # 4. Save artifact
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
        with open(output_path, 'wb') as f:
            f.write(resp.data)

        # 5. Assertions on the output
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

        output_midi = mido.MidiFile(output_path)
        output_note_on_count = _count_note_on(output_midi)

        assert output_note_on_count <= input_note_on_count, (
            f'Output has MORE note_on events ({output_note_on_count}) '
            f'than input ({input_note_on_count})'
        )
        assert output_note_on_count > 0, 'Output has no notes at all'

        output_tempo_count = _count_set_tempo(output_midi)
        assert output_tempo_count <= 3, (
            f'Expected few set_tempo events, got {output_tempo_count}'
        )
