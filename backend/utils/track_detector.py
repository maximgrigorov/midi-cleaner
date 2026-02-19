"""Track type detection and analysis utilities."""

import re
from collections import Counter
from config import (
    GUITAR_PATTERNS, VOCAL_PATTERNS, STRINGS_PATTERNS,
    BASS_PATTERNS, DRUM_PATTERNS, GUITAR_PROGRAMS,
)


def detect_track_type(track_name, program=None):
    """Detect the instrument type of a track.

    Returns one of: 'guitar', 'vocal', 'strings', 'bass', 'drums', 'other'
    """
    if track_name:
        name_lower = track_name.lower()
        for pattern in GUITAR_PATTERNS:
            if pattern in name_lower:
                return 'guitar'
        for pattern in VOCAL_PATTERNS:
            if pattern in name_lower:
                return 'vocal'
        for pattern in STRINGS_PATTERNS:
            if pattern in name_lower:
                return 'strings'
        for pattern in BASS_PATTERNS:
            if pattern in name_lower:
                return 'bass'
        for pattern in DRUM_PATTERNS:
            if pattern in name_lower:
                return 'drums'

    if program is not None and program in GUITAR_PROGRAMS:
        return 'guitar'

    return 'other'


def get_track_info(track, track_idx, ticks_per_beat):
    """Analyze a MIDI track and return a summary dict.

    Returns dict with:
        name, index, channel, program, track_type,
        note_count, note_range, channels_used, has_notes
    """
    name = ''
    channels = Counter()
    programs = {}
    note_count = 0
    min_note = 127
    max_note = 0

    for msg in track:
        if msg.type == 'track_name':
            name = msg.name
        elif msg.type == 'program_change':
            programs[msg.channel] = msg.program
        elif msg.type == 'note_on' and msg.velocity > 0:
            note_count += 1
            channels[msg.channel] += 1
            min_note = min(min_note, msg.note)
            max_note = max(max_note, msg.note)

    primary_channel = channels.most_common(1)[0][0] if channels else 0
    program = programs.get(primary_channel)
    track_type = detect_track_type(name, program)

    # Calculate duration
    total_ticks = sum(msg.time for msg in track)

    return {
        'name': name or f'Track {track_idx}',
        'index': track_idx,
        'channel': primary_channel,
        'program': program,
        'track_type': track_type,
        'note_count': note_count,
        'note_range': (min_note, max_note) if note_count > 0 else (0, 0),
        'channels_used': sorted(channels.keys()),
        'has_notes': note_count > 0,
        'total_ticks': total_ticks,
    }


def suggest_thresholds(track_type):
    """Suggest noise filter thresholds based on instrument type.

    Returns dict with min_duration_ticks and min_velocity.
    """
    suggestions = {
        'guitar': {'min_duration_ticks': 160, 'min_velocity': 25},
        'vocal': {'min_duration_ticks': 80, 'min_velocity': 15},
        'strings': {'min_duration_ticks': 100, 'min_velocity': 15},
        'bass': {'min_duration_ticks': 120, 'min_velocity': 20},
        'drums': {'min_duration_ticks': 30, 'min_velocity': 10},
        'other': {'min_duration_ticks': 120, 'min_velocity': 20},
    }
    return suggestions.get(track_type, suggestions['other'])
