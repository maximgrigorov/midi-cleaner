"""MIDI Cleaner — Flask web application for cleaning multi-track MIDI files."""

import os
import uuid
import json
import traceback

import mido
from flask import (
    Flask, request, jsonify, send_file,
    render_template, session,
)

from config import DEFAULT_CONFIG
from processors.pipeline import ProcessingPipeline
from utils.track_detector import get_track_info, suggest_thresholds
from utils.midi_analyzer import (
    analyze_track_for_notation,
    generate_playback_data,
)
from utils.midi_helpers import get_tempo

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'midi-cleaner-dev-key-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _get_session_dir():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    sid = session['session_id']
    path = os.path.join(UPLOAD_DIR, sid)
    os.makedirs(path, exist_ok=True)
    return path


def _load_midi(source='original'):
    """Helper: load a MidiFile from session path. Returns (mid, error_response)."""
    path_key = 'processed_path' if source == 'processed' else 'original_path'
    if path_key not in session:
        return None, (jsonify({'error': 'File not found'}), 404)
    file_path = session[path_key]
    if not os.path.exists(file_path):
        return None, (jsonify({'error': 'File not found on disk'}), 404)
    try:
        return mido.MidiFile(file_path), None
    except Exception as e:
        return None, (jsonify({'error': str(e)}), 500)


# ── Routes ──

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/upload', methods=['POST'])
def upload_midi():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': 'No file selected'}), 400
    if not f.filename.lower().endswith(('.mid', '.midi')):
        return jsonify({'error': 'File must be .mid or .midi'}), 400

    session_dir = _get_session_dir()
    original_name = f.filename
    file_id = str(uuid.uuid4())[:8]

    original_path = os.path.join(session_dir, f'{file_id}_original.mid')
    f.save(original_path)

    session['file_id'] = file_id
    session['original_name'] = original_name
    session['original_path'] = original_path
    # Clear any previous processed file
    session.pop('processed_path', None)

    try:
        mid = mido.MidiFile(original_path)
    except Exception as e:
        return jsonify({'error': f'Invalid MIDI file: {str(e)}'}), 400

    tracks_info = []
    for idx, track in enumerate(mid.tracks):
        info = get_track_info(track, idx, mid.ticks_per_beat)
        info['suggested_thresholds'] = suggest_thresholds(info['track_type'])
        info['note_range'] = list(info['note_range'])
        tracks_info.append(info)

    return jsonify({
        'file_id': file_id,
        'filename': original_name,
        'type': mid.type,
        'ticks_per_beat': mid.ticks_per_beat,
        'num_tracks': len(mid.tracks),
        'tracks': tracks_info,
    })


@app.route('/api/process', methods=['POST'])
def process_midi():
    if 'original_path' not in session:
        return jsonify({'error': 'No file uploaded. Please upload a MIDI file first.'}), 400

    original_path = session['original_path']
    if not os.path.exists(original_path):
        return jsonify({'error': 'Original file not found. Please re-upload.'}), 404

    try:
        config = json.loads(request.data) if request.data else {}
    except json.JSONDecodeError:
        config = {}

    full_config = dict(DEFAULT_CONFIG)
    for key, value in config.items():
        if key in full_config or key == 'track_overrides':
            full_config[key] = value

    try:
        mid = mido.MidiFile(original_path)
        pipeline = ProcessingPipeline(full_config)
        processed = pipeline.process(mid)

        session_dir = _get_session_dir()
        file_id = session.get('file_id', 'unknown')
        processed_path = os.path.join(session_dir, f'{file_id}_processed.mid')
        processed.save(processed_path)
        session['processed_path'] = processed_path

        tracks_info = []
        for idx, track in enumerate(processed.tracks):
            info = get_track_info(track, idx, processed.ticks_per_beat)
            info['note_range'] = list(info['note_range'])
            tracks_info.append(info)

        return jsonify({
            'success': True,
            'file_id': file_id,
            'tracks': tracks_info,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500


@app.route('/api/download')
def download_midi():
    if 'processed_path' not in session:
        return jsonify({'error': 'No processed file available'}), 404
    processed_path = session['processed_path']
    if not os.path.exists(processed_path):
        return jsonify({'error': 'Processed file not found'}), 404

    original_name = session.get('original_name', 'processed.mid')
    base, ext = os.path.splitext(original_name)
    download_name = f'{base}_cleaned{ext}'

    return send_file(
        processed_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='audio/midi',
    )


@app.route('/api/track/<int:track_idx>/notation')
def track_notation(track_idx):
    source = request.args.get('source', 'original')
    max_measures = int(request.args.get('measures', 64))

    mid, err = _load_midi(source)
    if err:
        return err
    if track_idx >= len(mid.tracks):
        return jsonify({'error': f'Track {track_idx} not found'}), 404

    try:
        track_info = get_track_info(mid.tracks[track_idx], track_idx,
                                    mid.ticks_per_beat)
        notation = analyze_track_for_notation(
            mid.tracks[track_idx], mid.ticks_per_beat, max_measures,
            track_type=track_info['track_type'],
        )
        return jsonify(notation)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/track/<int:track_idx>/playback')
def track_playback(track_idx):
    source = request.args.get('source', 'original')

    mid, err = _load_midi(source)
    if err:
        return err
    if track_idx >= len(mid.tracks):
        return jsonify({'error': f'Track {track_idx} not found'}), 404

    try:
        playback = generate_playback_data(mid.tracks[track_idx],
                                          mid.ticks_per_beat)
        # Get tempo from tempo track
        if mid.tracks:
            tempo = get_tempo(mid.tracks[0])
            playback['bpm'] = round(mido.tempo2bpm(tempo), 1)
        return jsonify(playback)
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/playback/all')
def all_tracks_playback():
    """Return playback data for all tracks combined (for the full player)."""
    source = request.args.get('source', 'original')

    mid, err = _load_midi(source)
    if err:
        return err

    try:
        bpm = 120.0
        if mid.tracks:
            tempo = get_tempo(mid.tracks[0])
            bpm = round(mido.tempo2bpm(tempo), 1)

        tracks = []
        total_duration = 0.0

        for idx, track in enumerate(mid.tracks):
            info = get_track_info(track, idx, mid.ticks_per_beat)
            if not info['has_notes']:
                continue
            pb = generate_playback_data(track, mid.ticks_per_beat)
            pb['bpm'] = bpm
            if pb['notes']:
                last = max(n['time'] + n['duration'] for n in pb['notes'])
                total_duration = max(total_duration, last)
            tracks.append({
                'index': idx,
                'name': info['name'],
                'track_type': info['track_type'],
                'notes': pb['notes'],
            })

        return jsonify({
            'bpm': bpm,
            'duration': round(total_duration, 2),
            'tracks': tracks,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
