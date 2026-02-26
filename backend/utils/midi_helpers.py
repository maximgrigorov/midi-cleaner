"""Common MIDI helper functions used across all processors."""

import mido
from config import NOTE_NAMES, VEXFLOW_NOTE_NAMES


def to_absolute_time(track):
    """Convert a track's delta times to absolute times.

    Returns list of (absolute_tick, message) tuples.
    """
    abs_time = 0
    result = []
    for msg in track:
        abs_time += msg.time
        result.append((abs_time, msg))
    return result


def to_delta_time(abs_messages):
    """Convert (absolute_tick, message) tuples back to a list of messages with delta times."""
    prev_time = 0
    result = []
    for abs_time, msg in abs_messages:
        delta = max(0, int(round(abs_time - prev_time)))
        result.append(msg.copy(time=delta))
        prev_time = abs_time
    return result


def extract_note_pairs(track):
    """Extract matched (note_on, note_off) pairs with absolute timing.

    Returns list of dicts:
        {
            'pitch': int,
            'channel': int,
            'velocity': int,
            'onset': int (absolute ticks),
            'offset': int (absolute ticks),
        }
    """
    abs_msgs = to_absolute_time(track)
    active = {}  # (channel, pitch) -> list of (onset_time, velocity)
    pairs = []

    for abs_time, msg in abs_msgs:
        if msg.type == 'note_on' and msg.velocity > 0:
            key = (msg.channel, msg.note)
            if key not in active:
                active[key] = []
            active[key].append((abs_time, msg.velocity))
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if key in active and active[key]:
                onset_time, velocity = active[key].pop(0)
                pairs.append({
                    'pitch': msg.note,
                    'channel': key[0],
                    'velocity': velocity,
                    'onset': onset_time,
                    'offset': abs_time,
                })

    # Handle orphaned note_on (no matching note_off) — close at last event time
    if abs_msgs:
        last_time = abs_msgs[-1][0]
        for key, pending in active.items():
            for onset_time, velocity in pending:
                pairs.append({
                    'pitch': key[1],
                    'channel': key[0],
                    'velocity': velocity,
                    'onset': onset_time,
                    'offset': last_time,
                })

    pairs.sort(key=lambda n: (n['onset'], n['pitch']))
    return pairs


def extract_non_note_messages(track):
    """Extract all non-note messages with absolute timing.

    Returns list of (absolute_tick, message) tuples for meta and CC messages.
    """
    abs_msgs = to_absolute_time(track)
    return [
        (t, msg) for t, msg in abs_msgs
        if msg.type not in ('note_on', 'note_off')
    ]


def rebuild_track_from_pairs(note_pairs, non_note_abs, channel=None):
    """Rebuild a MIDI track from note pairs and non-note messages.

    Args:
        note_pairs: list of note dicts with onset/offset/pitch/velocity/channel
        non_note_abs: list of (abs_time, msg) tuples for non-note messages
        channel: if set, force all notes to this channel

    Returns:
        mido.MidiTrack
    """
    # Build absolute-time event list
    events = []

    for note in note_pairs:
        ch = channel if channel is not None else note['channel']
        events.append((
            note['onset'],
            mido.Message('note_on', channel=ch, note=note['pitch'],
                         velocity=note['velocity'], time=0)
        ))
        events.append((
            note['offset'],
            mido.Message('note_off', channel=ch, note=note['pitch'],
                         velocity=0, time=0)
        ))

    events.extend(non_note_abs)

    # Sort by time, with meta messages and note_off before note_on at same tick
    def sort_key(item):
        t, msg = item
        # Priority: meta first, then note_off, then others, then note_on
        if msg.is_meta:
            order = 0
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            order = 1
        elif msg.type == 'note_on':
            order = 3
        else:
            order = 2
        return (t, order)

    events.sort(key=sort_key)

    # Convert to delta time
    track = mido.MidiTrack()
    prev_time = 0
    for abs_time, msg in events:
        delta = max(0, int(round(abs_time - prev_time)))
        track.append(msg.copy(time=delta))
        prev_time = abs_time

    return track


def midi_note_to_name(midi_note):
    """Convert MIDI note number to name like 'C4', 'D#5'."""
    octave = (midi_note // 12) - 1
    name = NOTE_NAMES[midi_note % 12]
    return f"{name}{octave}"


def midi_note_to_vexflow(midi_note):
    """Convert MIDI note number to VexFlow key format like 'c/4', 'd#/5'."""
    octave = (midi_note // 12) - 1
    name = VEXFLOW_NOTE_NAMES[midi_note % 12]
    return f"{name}/{octave}"


def ticks_to_duration_name(ticks, ticks_per_beat):
    """Convert tick duration to nearest standard duration name for VexFlow.

    Returns one of: 'w', 'h', 'q', '8', '16', '32'
    """
    if ticks_per_beat <= 0:
        return 'q'

    ratio = ticks / ticks_per_beat

    # Standard durations and their beat ratios
    durations = [
        (4.0, 'w'),       # whole
        (3.0, 'hd'),      # dotted half
        (2.0, 'h'),       # half
        (1.5, 'qd'),      # dotted quarter
        (1.0, 'q'),       # quarter
        (0.75, '8d'),     # dotted eighth
        (0.5, '8'),       # eighth
        (0.25, '16'),     # sixteenth
        (0.125, '32'),    # thirty-second
    ]

    # Find closest match
    best_name = 'q'
    best_diff = float('inf')
    for dur_ratio, name in durations:
        diff = abs(ratio - dur_ratio)
        if diff < best_diff:
            best_diff = diff
            best_name = name

    return best_name


def get_time_signature(track):
    """Extract time signature from a track. Returns (numerator, denominator) or (4, 4) default."""
    for msg in track:
        if msg.type == 'time_signature':
            return (msg.numerator, msg.denominator)
    return (4, 4)


def get_tempo(track):
    """Extract tempo from a track. Returns microseconds per beat, or 500000 (120 BPM) default."""
    for msg in track:
        if msg.type == 'set_tempo':
            return msg.tempo
    return 500000


def analyze_tempo_map(midi_file):
    """Analyze the tempo map across all tracks and return the dominant BPM.

    Collects every set_tempo event with its absolute tick position, then
    returns the tempo value that spans the most ticks (i.e. the dominant
    tempo).  Falls back to 120 BPM if no set_tempo events exist.

    Returns:
        float — dominant BPM rounded to 1 decimal place
    """
    # Collect all set_tempo events with absolute tick positions
    tempo_events = []
    for track in midi_file.tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == 'set_tempo':
                tempo_events.append((abs_tick, msg.tempo))

    if not tempo_events:
        return 120.0

    if len(tempo_events) == 1:
        return round(mido.tempo2bpm(tempo_events[0][1]), 1)

    # Sort by tick
    tempo_events.sort(key=lambda x: x[0])

    # Find the total length of the file (last event in any track)
    total_ticks = 0
    for track in midi_file.tracks:
        t = 0
        for msg in track:
            t += msg.time
        total_ticks = max(total_ticks, t)

    if total_ticks == 0:
        return round(mido.tempo2bpm(tempo_events[0][1]), 1)

    # Calculate how many ticks each tempo value spans
    tempo_durations = {}  # tempo_usec -> total_ticks
    for i, (tick, tempo) in enumerate(tempo_events):
        if i + 1 < len(tempo_events):
            span = tempo_events[i + 1][0] - tick
        else:
            span = total_ticks - tick
        span = max(0, span)
        tempo_durations[tempo] = tempo_durations.get(tempo, 0) + span

    # Pick the tempo with the longest span
    dominant_tempo = max(tempo_durations, key=tempo_durations.get)
    return round(mido.tempo2bpm(dominant_tempo), 1)


def get_key_signature(track):
    """Extract key signature from a track. Returns key string or 'C' default."""
    for msg in track:
        if msg.type == 'key_signature':
            return msg.key
    return 'C'


def calculate_bar_ticks(ticks_per_beat, time_sig=(4, 4)):
    """Calculate the number of ticks in one bar given time signature."""
    numerator, denominator = time_sig
    # ticks_per_beat = ticks per quarter note
    # One bar = numerator * (4/denominator) quarter notes
    return int(ticks_per_beat * numerator * 4 / denominator)
