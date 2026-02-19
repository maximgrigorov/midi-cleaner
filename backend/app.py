"""MIDI Cleaner — Flask web application for cleaning multi-track MIDI files."""

import os
import uuid
import json
import threading
import traceback

import mido
import mido.midifiles.meta as _mido_meta
from flask import (
    Flask, request, jsonify, send_file, session,
)
from flask_cors import CORS

# Patch mido to tolerate invalid key_signature events from AI-generated MIDI.
# Suno and other AI tools produce garbage key values (e.g. 17 sharps) that
# cause mido.MidiFile() to crash. We fall back to C major for invalid keys.
_orig_ks_decode = _mido_meta.MetaSpec_key_signature.decode

def _lenient_ks_decode(self, message, data):
    try:
        _orig_ks_decode(self, message, data)
    except _mido_meta.KeySignatureError:
        message.key = 'C'

_mido_meta.MetaSpec_key_signature.decode = _lenient_ks_decode

from config import DEFAULT_CONFIG
from processors.pipeline import ProcessingPipeline
from telemetry import PipelineContext
from optimizers.auto_tuner import AutoTuner, score_midi
from presets.presets import list_presets, get_preset_config, apply_preset, suggest_preset
from utils.track_detector import get_track_info, suggest_thresholds
from utils.midi_analyzer import (
    analyze_track_for_notation,
    generate_playback_data,
)
from utils.midi_helpers import get_tempo

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'midi-cleaner-dev-key-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:8080",
    "http://localhost:80",
    "http://localhost",
])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory report storage keyed by session_id
_reports: dict[str, dict] = {}
_reports_lock = threading.Lock()


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

@app.route('/docs/')
@app.route('/docs/<path:filename>')
def serve_docs(filename='README.md'):
    """Serve documentation markdown files rendered as HTML."""
    import markdown as _md

    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs')
    filepath = os.path.realpath(os.path.join(docs_dir, filename))
    if not filepath.startswith(os.path.realpath(docs_dir)) or not os.path.exists(filepath):
        return 'Not found', 404
    with open(filepath) as f:
        raw = f.read()

    body_html = _md.markdown(raw, extensions=['tables', 'fenced_code', 'toc', 'attr_list'])

    # Build sidebar nav from doc files
    doc_files = sorted(
        f for f in os.listdir(docs_dir)
        if f.endswith('.md') and f != 'README.md'
    )
    nav_items = '<li class="docs-nav-item"><a href="/docs/">Home</a></li>\n'
    for df in doc_files:
        label = df.replace('.md', '').split('_', 1)[-1].replace('_', ' ').title()
        if df.startswith('0'):
            label = df.replace('.md', '')[3:].replace('_', ' ').title()
        active = ' class="active"' if df == filename else ''
        nav_items += f'<li class="docs-nav-item"><a href="/docs/{df}"{active}>{label}</a></li>\n'

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MIDI Cleaner — Docs</title>
<style>
:root {{
  --bg: #0f1117; --surface: #1a1d27; --surface2: #232733;
  --border: #2d3140; --text: #e1e4ed; --text-muted: #8b90a0;
  --accent: #4f8cff; --accent-hover: #6ba0ff;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.7;
}}
.docs-layout {{
  display: flex; min-height: 100vh;
}}
.docs-sidebar {{
  width: 260px; background: var(--surface); border-right: 1px solid var(--border);
  padding: 24px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto;
  flex-shrink: 0;
}}
.docs-sidebar-header {{
  padding: 0 20px 16px; border-bottom: 1px solid var(--border); margin-bottom: 12px;
}}
.docs-sidebar-header a {{
  color: var(--accent); text-decoration: none; font-weight: 600; font-size: 15px;
}}
.docs-sidebar-header a:hover {{ color: var(--accent-hover); }}
.docs-nav {{ list-style: none; }}
.docs-nav-item a {{
  display: block; padding: 8px 20px; color: var(--text-muted);
  text-decoration: none; font-size: 14px; transition: background 0.15s, color 0.15s;
}}
.docs-nav-item a:hover {{ background: var(--surface2); color: var(--text); }}
.docs-nav-item a.active {{ color: var(--accent); background: var(--surface2); border-left: 3px solid var(--accent); }}
.docs-content {{
  flex: 1; max-width: 820px; margin: 0 auto; padding: 40px 48px;
}}
.docs-content h1 {{ font-size: 2em; margin-bottom: 16px; color: #fff; }}
.docs-content h2 {{ font-size: 1.5em; margin-top: 40px; margin-bottom: 12px; color: #fff; padding-bottom: 6px; border-bottom: 1px solid var(--border); }}
.docs-content h3 {{ font-size: 1.2em; margin-top: 28px; margin-bottom: 8px; color: var(--text); }}
.docs-content p {{ margin-bottom: 14px; }}
.docs-content ul, .docs-content ol {{ margin-bottom: 14px; padding-left: 24px; }}
.docs-content li {{ margin-bottom: 6px; }}
.docs-content a {{ color: var(--accent); text-decoration: none; }}
.docs-content a:hover {{ text-decoration: underline; }}
.docs-content strong {{ color: #fff; }}
.docs-content code {{
  background: var(--surface2); padding: 2px 6px; border-radius: 4px; font-size: 0.9em;
  color: var(--accent);
}}
.docs-content pre {{
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
  padding: 16px; overflow-x: auto; margin-bottom: 16px;
}}
.docs-content pre code {{ background: none; padding: 0; color: var(--text); }}
.docs-content hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
.docs-content blockquote {{
  border-left: 3px solid var(--accent); padding: 8px 16px; margin: 14px 0;
  background: var(--surface); border-radius: 0 6px 6px 0; color: var(--text-muted);
}}
.docs-content table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
.docs-content th, .docs-content td {{
  border: 1px solid var(--border); padding: 8px 12px; text-align: left;
}}
.docs-content th {{ background: var(--surface2); color: #fff; }}
.docs-content img {{ max-width: 100%; border-radius: 8px; margin: 12px 0; }}
@media (max-width: 768px) {{
  .docs-layout {{ flex-direction: column; }}
  .docs-sidebar {{ width: 100%; height: auto; position: static; border-right: none; border-bottom: 1px solid var(--border); padding: 12px 0; }}
  .docs-content {{ padding: 24px 16px; }}
}}
</style>
</head>
<body>
<div class="docs-layout">
  <nav class="docs-sidebar">
    <div class="docs-sidebar-header">
      <a href="/">&#8592; Back to App</a>
    </div>
    <ul class="docs-nav">
      {nav_items}
    </ul>
  </nav>
  <article class="docs-content">
    {body_html}
  </article>
</div>
</body>
</html>'''
    return page


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
            if isinstance(full_config.get(key), dict) and isinstance(value, dict):
                full_config[key] = {**full_config[key], **value}
            else:
                full_config[key] = value

    preset_name = config.pop('_preset', '')

    try:
        mid = mido.MidiFile(original_path)
        original_name = session.get('original_name', '')

        ctx = PipelineContext(file_name=original_name, config=full_config)
        if preset_name:
            ctx.report.preset_applied = preset_name

        pipeline = ProcessingPipeline(full_config, context=ctx)
        processed = pipeline.process(mid)

        report = ctx.report

        session_dir = _get_session_dir()
        file_id = session.get('file_id', 'unknown')
        processed_path = os.path.join(session_dir, f'{file_id}_processed.mid')
        processed.save(processed_path)
        session['processed_path'] = processed_path

        sid = session.get('session_id', '')
        with _reports_lock:
            _reports[sid] = report.to_dict()

        tracks_info = []
        for idx, track in enumerate(processed.tracks):
            info = get_track_info(track, idx, processed.ticks_per_beat)
            info['note_range'] = list(info['note_range'])
            tracks_info.append(info)

        return jsonify({
            'success': True,
            'file_id': file_id,
            'tracks': tracks_info,
            'report': report.to_dict(),
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


@app.route('/api/report')
def get_report():
    """Return the telemetry report for the last processing run."""
    sid = session.get('session_id', '')
    with _reports_lock:
        report = _reports.get(sid)
    if not report:
        return jsonify({'error': 'No report available. Process a file first.'}), 404
    return jsonify(report)


@app.route('/api/report/download')
def download_report():
    """Download the telemetry report as report.json."""
    sid = session.get('session_id', '')
    with _reports_lock:
        report = _reports.get(sid)
    if not report:
        return jsonify({'error': 'No report available'}), 404
    import io
    buf = io.BytesIO(json.dumps(report, indent=2).encode('utf-8'))
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name='report.json',
                     mimetype='application/json')


@app.route('/api/presets')
def api_presets():
    """List available presets."""
    return jsonify({'presets': list_presets()})


@app.route('/api/presets/<preset_id>')
def api_preset_config(preset_id):
    """Return config overrides for a specific preset."""
    cfg = get_preset_config(preset_id)
    if not cfg:
        return jsonify({'error': 'Preset not found'}), 404
    return jsonify({'config': cfg})


@app.route('/api/presets/suggest')
def api_suggest_preset():
    """Suggest a preset based on detected track type."""
    mid, err = _load_midi('original')
    if err:
        return err
    from optimizers.auto_tuner import detect_dominant_track_type
    track_type = detect_dominant_track_type(mid)
    preset_id = suggest_preset(track_type)
    cfg = get_preset_config(preset_id) if preset_id else {}
    return jsonify({
        'track_type': track_type,
        'preset_id': preset_id or '',
        'config': cfg,
    })


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


# ── Optimization state (per-session, in-memory) ──

_optimize_state: dict[str, dict] = {}
_optimize_lock = threading.Lock()


def _run_optimization(session_id: str, midi_path: str, max_trials: int,
                      llm_config: dict | None = None):
    """Background worker for optimization."""
    try:
        mid = mido.MidiFile(midi_path)

        def on_trial(tr):
            with _optimize_lock:
                st = _optimize_state.get(session_id)
                if st:
                    st['current_trial'] = tr.number + 1
                    st['best_score'] = max(st['best_score'], tr.score)
                    st['current_params'] = tr.params
                    st['trials'].append({
                        'number': tr.number,
                        'score': tr.score,
                        'params': tr.params,
                        'metrics': tr.metrics,
                    })

        llm_advisor = None
        if llm_config and llm_config.get('enabled'):
            try:
                import logging as _log
                from llm.guidance import LLMAdvisor
                _llm_defaults = DEFAULT_CONFIG.get('llm', {})
                _api_base = llm_config.get('api_base') or _llm_defaults.get('api_base', '')
                _model = llm_config.get('model') or _llm_defaults.get('model', 'gpt-4o-mini')
                _log.getLogger(__name__).info(
                    '[LLM] Advisor enabled: api_base=%s model=%s', _api_base, _model
                )
                llm_advisor = LLMAdvisor(
                    api_base=_api_base,
                    model=_model,
                    max_calls=llm_config.get('max_calls') or _llm_defaults.get('max_calls', 3),
                    max_tokens=llm_config.get('max_tokens') or _llm_defaults.get('max_tokens', 600),
                    enabled=True,
                )
            except Exception:
                pass

        tuner = AutoTuner(mid, max_trials=max_trials, callback=on_trial,
                          llm_advisor=llm_advisor)

        with _optimize_lock:
            st = _optimize_state.get(session_id)
            if st:
                st['track_type'] = tuner.track_type

        result = tuner.optimize()

        ctx = PipelineContext(config=result.best_config)
        pipeline = ProcessingPipeline(result.best_config, context=ctx)
        processed = pipeline.process(mid)

        session_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        optimized_path = os.path.join(session_dir, 'optimized.mid')
        processed.save(optimized_path)

        report = ctx.report
        report.best_params = result.best_params
        report.optimizer_history = [
            {'number': t.number, 'score': t.score, 'params': t.params}
            for t in result.trials
        ]
        report.llm_decisions = result.llm_decisions

        with _optimize_lock:
            st = _optimize_state.get(session_id)
            if st:
                st['status'] = 'done'
                st['best_score'] = result.best_score
                st['best_params'] = result.best_params
                st['best_config'] = result.best_config
                st['stop_reason'] = result.stop_reason
                st['optimized_path'] = optimized_path
                st['total_trials'] = len(result.trials)
                st['llm_decisions'] = result.llm_decisions

        with _reports_lock:
            _reports[session_id] = report.to_dict()

    except Exception as e:
        traceback.print_exc()
        with _optimize_lock:
            st = _optimize_state.get(session_id)
            if st:
                st['status'] = 'error'
                st['error'] = str(e)


@app.route('/api/optimize', methods=['POST'])
def start_optimization():
    if 'original_path' not in session:
        return jsonify({'error': 'No file uploaded. Please upload a MIDI file first.'}), 400

    original_path = session['original_path']
    if not os.path.exists(original_path):
        return jsonify({'error': 'Original file not found. Please re-upload.'}), 404

    sid = session.get('session_id', str(uuid.uuid4()))

    try:
        body = json.loads(request.data) if request.data else {}
    except json.JSONDecodeError:
        body = {}
    max_trials = min(int(body.get('max_trials', 40)), 100)
    llm_cfg = body.get('llm', DEFAULT_CONFIG.get('llm', {}))

    with _optimize_lock:
        existing = _optimize_state.get(sid)
        if existing and existing.get('status') == 'running':
            return jsonify({'error': 'Optimization already in progress'}), 409

        _optimize_state[sid] = {
            'status': 'running',
            'current_trial': 0,
            'total_trials': max_trials,
            'best_score': float('-inf'),
            'best_params': {},
            'best_config': {},
            'current_params': {},
            'track_type': '',
            'trials': [],
            'stop_reason': '',
            'error': None,
            'optimized_path': None,
            'llm_decisions': [],
        }

    t = threading.Thread(
        target=_run_optimization,
        args=(sid, original_path, max_trials, llm_cfg),
        daemon=True,
    )
    t.start()

    return jsonify({'status': 'started', 'max_trials': max_trials})


@app.route('/api/optimize/status')
def optimization_status():
    sid = session.get('session_id')
    if not sid:
        return jsonify({'error': 'No session'}), 400

    with _optimize_lock:
        st = _optimize_state.get(sid)

    if not st:
        return jsonify({'status': 'idle'})

    resp = {
        'status': st['status'],
        'current_trial': st['current_trial'],
        'total_trials': st['total_trials'],
        'best_score': st['best_score'] if st['best_score'] != float('-inf') else None,
        'best_params': st['best_params'],
        'current_params': st['current_params'],
        'track_type': st['track_type'],
        'stop_reason': st['stop_reason'],
        'trials': st['trials'],
    }
    if st.get('error'):
        resp['error'] = st['error']
    if st.get('best_config'):
        resp['best_config'] = st['best_config']
    if st.get('llm_decisions'):
        resp['llm_decisions'] = st['llm_decisions']

    return jsonify(resp)


@app.route('/api/optimize/apply', methods=['POST'])
def apply_optimized():
    """Return best params so the UI can apply them to the config controls.

    Does NOT set processed_path — the user must still click "Process & Clean"
    to generate the actual output file with these parameters.
    """
    sid = session.get('session_id')
    if not sid:
        return jsonify({'error': 'No session'}), 400

    with _optimize_lock:
        st = _optimize_state.get(sid)

    if not st or st['status'] != 'done':
        return jsonify({'error': 'No completed optimization'}), 400

    return jsonify({
        'success': True,
        'best_params': st['best_params'],
        'best_score': st['best_score'],
    })


if __name__ == '__main__':
    import logging as _logging
    _log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    _logging.basicConfig(
        level=getattr(_logging, _log_level, _logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )
    # Always show LLM traffic in logs
    _logging.getLogger('llm.guidance').setLevel(_logging.DEBUG)
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
