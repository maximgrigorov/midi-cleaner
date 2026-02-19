"""Pitch Cluster Processor — merges near-pitch notes that occur almost simultaneously.

Cleans transcription noise typical for AI-generated MIDI (especially FX tracks)
where the same musical event is represented as a tight bundle of slightly different
pitches all firing within a short time window.

This is NOT quantization and NOT voice merging — it operates purely on pitch
proximity within a configurable time window, collapsing each cluster to a single
representative note.

Config (nested under 'pitch_cluster' key):
    enabled           (bool, default True)  — enable/disable processor
    time_window_ticks (int,  default 80)    — max onset spread within a cluster (ticks)
    pitch_threshold   (int,  default 1)     — max semitone distance within a cluster
"""

import bisect
from collections import defaultdict
from typing import Any

from utils.midi_helpers import (
    extract_note_pairs,
    extract_non_note_messages,
    rebuild_track_from_pairs,
)


class PitchClusterProcessor:
    """Merge near-pitch notes that start almost simultaneously into a single note.

    For each channel independently, notes are scanned in onset order.  When a
    group of notes falls within *time_window_ticks* of each other AND within
    *pitch_threshold* semitones of the seed note's pitch, they form a cluster.
    The cluster is replaced by whichever note wins the selection rule:
        1. highest velocity
        2. longest duration
        3. lowest pitch distance from cluster median pitch
    """

    def __init__(self, config: dict) -> None:
        cfg = config.get('pitch_cluster', {})
        self.enabled: bool = cfg.get('enabled', True)
        self.time_window: int = cfg.get('time_window_ticks', 80)
        self.pitch_threshold: int = cfg.get('pitch_threshold', 1)

    def process(self, track, ticks_per_beat: int):
        """Process a single track: collapse pitch clusters to one note each.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution (unused here but kept for API consistency)

        Returns:
            mido.MidiTrack — processed track (original untouched when disabled)
        """
        if not self.enabled:
            return track

        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)

        if not note_pairs:
            return track

        # Process each MIDI channel independently — never merge across channels
        by_channel: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for note in note_pairs:
            by_channel[note['channel']].append(note)

        result: list[dict[str, Any]] = []
        for notes in by_channel.values():
            result.extend(self._cluster_channel(notes))

        result.sort(key=lambda n: (n['onset'], n['pitch']))
        return rebuild_track_from_pairs(result, non_notes)

    # ── internal ────────────────────────────────────────────────────────────

    def _cluster_channel(self, notes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Detect and collapse pitch clusters within a single MIDI channel.

        Algorithm (O(n log n)):
          1. Sort notes by onset then pitch.
          2. Maintain a boolean visited[] array.
          3. For each unvisited seed note N, use bisect to locate all notes
             whose onset falls within [N.onset - window, N.onset + window],
             then keep only those within pitch_threshold semitones of N.pitch.
          4. Mark all cluster members visited; emit winner.
        """
        # Sort by onset for binary-search window scanning
        sorted_notes = sorted(notes, key=lambda n: (n['onset'], n['pitch']))
        total = len(sorted_notes)
        visited = [False] * total

        # Separate onset list allows O(log n) range queries via bisect
        onsets = [n['onset'] for n in sorted_notes]

        result: list[dict[str, Any]] = []

        for i in range(total):
            if visited[i]:
                continue

            seed = sorted_notes[i]

            # Binary-search bounds for onset window
            lo = bisect.bisect_left(onsets, seed['onset'] - self.time_window)
            hi = bisect.bisect_right(onsets, seed['onset'] + self.time_window)

            # Collect cluster: unvisited notes within onset window AND pitch range
            cluster_idx = [
                j for j in range(lo, hi)
                if not visited[j]
                and abs(sorted_notes[j]['pitch'] - seed['pitch']) <= self.pitch_threshold
            ]

            # Mark every cluster member as processed
            for j in cluster_idx:
                visited[j] = True

            if len(cluster_idx) == 1:
                # Trivial cluster — keep the note unchanged
                result.append(seed)
            else:
                cluster = [sorted_notes[j] for j in cluster_idx]
                result.append(self._select_winner(cluster))

        return result

    def _select_winner(self, cluster: list[dict[str, Any]]) -> dict[str, Any]:
        """Choose the single surviving note from a cluster.

        Selection priority (lexicographic, lower = better):
            1. velocity  — higher is better  → negate for min()
            2. duration  — longer is better  → negate for min()
            3. pitch dist from cluster median — smaller is better
        """
        pitches = sorted(n['pitch'] for n in cluster)
        # Integer median: lower-middle element for even-length lists
        median_pitch = pitches[len(pitches) // 2]

        def _key(n: dict[str, Any]) -> tuple[int, int, int]:
            duration = n['offset'] - n['onset']
            pitch_dist = abs(n['pitch'] - median_pitch)
            return (-n['velocity'], -duration, pitch_dist)

        return min(cluster, key=_key)
