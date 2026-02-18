"""Voice Merger — consolidates all MIDI channels/voices within a track into one voice.

Guitar Pro exports may place different voices on separate MIDI channels within the
same track. This processor reassigns every note to the track's primary channel and
resolves overlapping notes of the same pitch that result from the merge.

Additionally, aligns chord durations so that simultaneously-starting notes have
the same duration — this prevents Guitar Pro from splitting them into separate voices.
"""

from collections import Counter, defaultdict

from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
)


class VoiceMerger:
    """Merge all voices in a track to voice 1 (primary channel)."""

    def __init__(self, config):
        self.enabled = config.get('merge_voices', True)
        self.remove_overlaps = config.get('remove_overlaps', True)

    def process(self, track, ticks_per_beat):
        """Process a single track: merge voices and resolve overlaps.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution

        Returns:
            mido.MidiTrack — processed track
        """
        if not self.enabled:
            return track

        # Determine primary channel
        primary_channel = self._find_primary_channel(track)

        # Extract note pairs and non-note messages
        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)

        if not note_pairs:
            return track

        # Reassign all notes to primary channel
        for note in note_pairs:
            note['channel'] = primary_channel

        # Resolve overlapping same-pitch notes
        if self.remove_overlaps:
            note_pairs = self._resolve_overlaps(note_pairs)

        # Align chord durations: notes starting at same tick get same duration
        # This prevents Guitar Pro from creating multiple voices
        note_pairs = self._align_chord_durations(note_pairs)

        # Force non-note channel messages to primary channel too
        fixed_non_notes = []
        for abs_time, msg in non_notes:
            if hasattr(msg, 'channel') and not msg.is_meta:
                fixed_non_notes.append((abs_time, msg.copy(channel=primary_channel)))
            else:
                fixed_non_notes.append((abs_time, msg))

        return rebuild_track_from_pairs(note_pairs, fixed_non_notes, channel=primary_channel)

    def _find_primary_channel(self, track):
        """Find the most-used channel in the track."""
        channels = Counter()
        for msg in track:
            if msg.type in ('note_on', 'note_off'):
                channels[msg.channel] += 1
        if channels:
            return channels.most_common(1)[0][0]
        return 0

    def _resolve_overlaps(self, note_pairs):
        """Merge overlapping notes of the same pitch on the same channel.

        When two notes with the same pitch overlap, merge them into one note
        spanning the full duration (earliest onset to latest offset).
        """
        # Group by (channel, pitch)
        groups = defaultdict(list)
        for note in note_pairs:
            groups[(note['channel'], note['pitch'])].append(note)

        merged = []
        for key, notes in groups.items():
            notes.sort(key=lambda n: n['onset'])
            current = notes[0].copy()

            for next_note in notes[1:]:
                # Check overlap: next note starts before current ends
                if next_note['onset'] < current['offset']:
                    # Merge: extend duration, keep higher velocity
                    current['offset'] = max(current['offset'], next_note['offset'])
                    current['velocity'] = max(current['velocity'], next_note['velocity'])
                else:
                    merged.append(current)
                    current = next_note.copy()

            merged.append(current)

        merged.sort(key=lambda n: (n['onset'], n['pitch']))
        return merged

    def _align_chord_durations(self, note_pairs):
        """Align durations of simultaneously-starting notes (chords).

        Guitar Pro assigns notes to different voices when they start at the same
        beat but have different durations. By aligning all chord-note durations to
        the shortest note in the chord, all notes stay in Voice 1.

        Uses the SHORTEST duration in each chord group to prevent bar overflow.
        """
        by_onset = defaultdict(list)
        for note in note_pairs:
            by_onset[note['onset']].append(note)

        result = []
        for onset, notes in sorted(by_onset.items()):
            if len(notes) > 1:
                # Check if there are actually different durations
                durations = [n['offset'] - n['onset'] for n in notes]
                if len(set(durations)) > 1:
                    # Use shortest duration for all notes in chord
                    shortest = min(durations)
                    for note in notes:
                        note['offset'] = note['onset'] + shortest
            result.extend(notes)

        result.sort(key=lambda n: (n['onset'], n['pitch']))
        return result
