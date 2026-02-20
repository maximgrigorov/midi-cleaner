"""MIDI analysis for notation rendering and playback data generation."""

from itertools import groupby
import mido
from utils.midi_helpers import (
    extract_note_pairs,
    midi_note_to_name,
    midi_note_to_vexflow,
    ticks_to_duration_name,
    get_time_signature,
    get_tempo,
    calculate_bar_ticks,
)

# ── Guitar TAB tuning (string number → open MIDI note) ──
GUITAR_TUNING = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}


def analyze_track_for_notation(track, ticks_per_beat, max_measures=64,
                               track_type='other'):
    """Convert a MIDI track into notation data suitable for VexFlow rendering.

    For guitar-type tracks, returns treble clef + TAB positions.
    """
    time_sig = get_time_signature(track)
    bar_ticks = calculate_bar_ticks(ticks_per_beat, time_sig)
    notes = extract_note_pairs(track)

    if not notes:
        return {
            'clef': 'treble',
            'time_signature': list(time_sig),
            'measures': [],
            'show_tab': False,
        }

    is_guitar = track_type in ('guitar',)

    # Guitar always uses treble clef; others auto-detect
    if is_guitar:
        clef = 'treble'
    else:
        avg_pitch = sum(n['pitch'] for n in notes) / len(notes)
        clef = 'treble' if avg_pitch >= 55 else 'bass'

    # Group notes into measures
    measures = []
    for measure_idx in range(max_measures):
        bar_start = measure_idx * bar_ticks
        bar_end = bar_start + bar_ticks

        bar_notes = [
            n for n in notes
            if n['onset'] >= bar_start and n['onset'] < bar_end
        ]

        if not bar_notes and bar_start > (notes[-1]['onset'] if notes else 0):
            break

        measure_data = _build_measure(bar_notes, bar_start, bar_ticks,
                                      ticks_per_beat, clef, is_guitar)
        measures.append(measure_data)

    return {
        'clef': clef,
        'time_signature': list(time_sig),
        'measures': measures,
        'show_tab': is_guitar,
    }


def _build_measure(notes, bar_start, bar_ticks, ticks_per_beat, clef,
                   include_tab=False):
    """Build notation data for a single measure."""
    if not notes:
        rest_dur = ticks_to_duration_name(bar_ticks, ticks_per_beat)
        return {
            'notes': [{
                'keys': ['b/4'] if clef == 'treble' else ['d/3'],
                'duration': _ensure_rest_duration(rest_dur),
                'is_rest': True,
                'tab': [],
            }]
        }

    sorted_notes = sorted(notes, key=lambda n: n['onset'])
    events = []

    for onset, group in groupby(sorted_notes, key=lambda n: n['onset']):
        chord_notes = list(group)
        rel_onset = onset - bar_start

        min_dur_ticks = min(n['offset'] - n['onset'] for n in chord_notes)
        max_possible = bar_ticks - rel_onset
        dur_ticks = min(min_dur_ticks, max_possible)
        dur_ticks = max(dur_ticks, 1)

        dur_name = ticks_to_duration_name(dur_ticks, ticks_per_beat)

        # Deduplicate keys
        seen = set()
        keys = []
        midi_pitches = []
        for n in chord_notes:
            k = midi_note_to_vexflow(n['pitch'])
            if k not in seen:
                seen.add(k)
                keys.append(k)
                midi_pitches.append(n['pitch'])
        keys.sort(key=lambda k: _vexflow_key_to_midi_approx(k))
        midi_pitches.sort()
        if len(keys) > 6:
            keys = keys[:6]
            midi_pitches = midi_pitches[:6]

        # TAB positions for guitar
        tab = _midi_notes_to_tab(midi_pitches) if include_tab else []

        events.append({
            'onset_ticks': rel_onset,
            'duration_ticks': dur_ticks,
            'keys': keys,
            'duration': dur_name,
            'is_rest': False,
            'tab': tab,
        })

    filled_events = _fill_rests(events, bar_ticks, ticks_per_beat, clef)
    return {'notes': filled_events}


def _midi_notes_to_tab(midi_pitches):
    """Convert MIDI pitches to guitar TAB positions [{str, fret}, ...]."""
    sorted_notes = sorted(midi_pitches)
    positions = []
    used_strings = set()

    for note in sorted_notes:
        best = None
        # Try strings low to high (6→1) for natural voicing
        for s in [6, 5, 4, 3, 2, 1]:
            if s in used_strings:
                continue
            fret = note - GUITAR_TUNING[s]
            if 0 <= fret <= 24:
                best = {'str': s, 'fret': fret}
                break
        if best:
            positions.append(best)
            used_strings.add(best['str'])

    return positions


def _fill_rests(events, bar_ticks, ticks_per_beat, clef):
    """Insert rest events to fill gaps between notes in a measure."""
    result = []
    current_tick = 0
    rest_key = 'b/4' if clef == 'treble' else 'd/3'

    for event in events:
        onset = event['onset_ticks']
        gap = onset - current_tick
        if gap > 0:
            rest_dur = ticks_to_duration_name(gap, ticks_per_beat)
            result.append({
                'keys': [rest_key],
                'duration': _ensure_rest_duration(rest_dur),
                'is_rest': True,
                'tab': [],
            })

        result.append({
            'keys': event['keys'],
            'duration': event['duration'],
            'is_rest': event['is_rest'],
            'tab': event.get('tab', []),
        })
        current_tick = onset + event['duration_ticks']

    remaining = bar_ticks - current_tick
    if remaining > ticks_per_beat * 0.1:
        rest_dur = ticks_to_duration_name(remaining, ticks_per_beat)
        result.append({
            'keys': [rest_key],
            'duration': _ensure_rest_duration(rest_dur),
            'is_rest': True,
            'tab': [],
        })

    return result


def _ensure_rest_duration(dur_name):
    if dur_name.endswith('r'):
        return dur_name
    return dur_name + 'r'


def _vexflow_key_to_midi_approx(key):
    parts = key.split('/')
    if len(parts) != 2:
        return 60
    note_name = parts[0].lower()
    try:
        octave = int(parts[1])
    except ValueError:
        octave = 4
    pitch_map = {
        'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3,
        'e': 4, 'f': 5, 'f#': 6, 'gb': 6, 'g': 7, 'g#': 8,
        'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11,
    }
    base = pitch_map.get(note_name, 0)
    return (octave + 1) * 12 + base


def generate_playback_data(track, ticks_per_beat):
    """Generate playback data for Tone.js."""
    tempo = get_tempo(track)
    bpm = mido.tempo2bpm(tempo)
    notes = extract_note_pairs(track)
    playback = []

    for n in notes:
        onset_beats = n['onset'] / ticks_per_beat
        duration_beats = max((n['offset'] - n['onset']) / ticks_per_beat, 0.05)
        onset_seconds = onset_beats * (60.0 / bpm)
        duration_seconds = duration_beats * (60.0 / bpm)
        playback.append({
            'pitch': n['pitch'],
            'note': midi_note_to_name(n['pitch']),
            'time': round(onset_seconds, 4),
            'duration': round(duration_seconds, 4),
            'velocity': n['velocity'],
        })

    return {
        'bpm': round(bpm, 1),
        'notes': playback,
    }
