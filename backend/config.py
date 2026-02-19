"""Default configuration for MIDI Cleaner application."""

DEFAULT_CONFIG = {
    # Tempo deduplication (removes redundant set_tempo events)
    'tempo_deduplicator': {'enabled': True},

    # Voice merging
    'merge_voices': True,
    'remove_overlaps': True,

    # Triplet handling
    'remove_triplets': True,
    'triplet_tolerance': 0.15,  # 15% tolerance for triplet detection

    # Quantization
    'quantize': True,
    'quantize_grid': 'eighth',  # 'quarter', 'eighth', 'sixteenth'

    # CC message removal
    'remove_cc': True,
    'cc_numbers': [64, 68],  # 64=sustain, 68=legato

    # Pitch cluster (merge near-pitch simultaneous notes)
    'pitch_cluster': {
        'enabled': True,
        'time_window_ticks': 20,
        'pitch_threshold': 1,
    },

    # Noise filter
    'filter_noise': True,
    'min_duration_ticks': 120,
    'min_velocity': 20,

    # Same-pitch overlap resolver
    'same_pitch_overlap_resolver': {'enabled': True},

    # Processing range (1-indexed bar numbers)
    'start_bar': 1,

    # Track flattener (merge all tracks into a single MTrk)
    'merge_tracks': {
        'enabled': False,
        'include_cc': False,
        'cc_whitelist': [64, 68],
    },

    # Per-track overrides: { track_index: { param: value, ... } }
    'track_overrides': {},

    # LLM guidance (optional).
    # Inside a podman container, the host is reachable via host.containers.internal
    # (requires --add-host=host.containers.internal:host-gateway on podman run).
    # When running outside a container (dev mode) you can override with LLM_API_BASE env var.
    'llm': {
        'enabled': True,
        'api_base': 'http://host.containers.internal:4000',
        'model': 'gpt-4o-mini',
        'max_calls': 3,
        'max_tokens': 600,
    },
}

# Quantization grid divisors (relative to ticks_per_beat = 1 quarter note)
GRID_DIVISORS = {
    'whole': 0.25,
    'half': 0.5,
    'quarter': 1,
    'eighth': 2,
    'sixteenth': 4,
    'thirtysecond': 8,
}

# Standard MIDI note names
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# VexFlow-friendly note names (flats converted to sharps)
VEXFLOW_NOTE_NAMES = ['c', 'c#', 'd', 'd#', 'e', 'f', 'f#', 'g', 'g#', 'a', 'a#', 'b']

# Known guitar MIDI program numbers (0-indexed)
GUITAR_PROGRAMS = set(range(24, 32))  # 24-31 = guitar family

# Track name patterns for auto-detection
GUITAR_PATTERNS = ['guitar', 'gtr', 'git', 'guit', 'distortion', 'overdrive', 'lead', 'rhythm']
VOCAL_PATTERNS = ['vocal', 'vox', 'voice', 'sing', 'choir']
STRINGS_PATTERNS = ['string', 'violin', 'viola', 'cello', 'orchestra']
BASS_PATTERNS = ['bass', 'bas']
DRUM_PATTERNS = ['drum', 'perc', 'kit']
