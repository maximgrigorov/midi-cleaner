"""Processing Pipeline — orchestrates all MIDI processors in the correct order.

Processing order (per-track):
  0. Tempo Dedup              — remove redundant set_tempo meta events (all tracks)
  1. Pitch Cluster            — merge near-pitch simultaneous notes (AI transcription noise)
  2. Voice Merger             — consolidate channels to one voice, align chord durations
  3. CC Filter                — remove sustain/legato CC messages
  4. Triplet Remover          — convert triplet durations to straight eighths
  5. Quantizer                — snap onset times and durations to grid (bar-aware)
  6. Noise Filter             — remove short/quiet parasitic notes
  7. Same-Pitch Overlap Resolver — deduplicate overlapping same-pitch notes (per channel)
  8. Meta Cleanup             — strip stray tempo/time-sig events from data tracks

Post-processing (file-level):
  9. Merge Tracks             — optionally flatten all tracks into a single MTrk
"""

import copy
import time
from collections import defaultdict

import mido

from processors.tempo_deduplicator import TempoDeduplicator
from processors.pitch_cluster import PitchClusterProcessor
from processors.voice_merger import VoiceMerger
from processors.triplet_remover import TripletRemover
from processors.quantizer import Quantizer
from processors.cc_filter import CCFilter
from processors.noise_filter import NoiseFilter
from processors.same_pitch_overlap_resolver import SamePitchOverlapResolver
from processors.merge_tracks_to_single import MergeTracksToSingleTrack
from telemetry import PipelineContext, count_notes, count_notes_midi
from utils.midi_helpers import (
    get_time_signature, calculate_bar_ticks,
    extract_note_pairs, extract_non_note_messages, rebuild_track_from_pairs,
)
from utils.track_detector import get_track_info


class ProcessingPipeline:
    """Main MIDI processing pipeline."""

    CONDUCTOR_ONLY_META = {'set_tempo', 'time_signature'}

    def __init__(self, config, context: PipelineContext | None = None):
        self.config = config
        self.start_bar = config.get('start_bar', 1)
        self.ctx = context or PipelineContext(config=config)

    def process(self, midi_file):
        """Process an entire MIDI file.

        Args:
            midi_file: mido.MidiFile

        Returns:
            mido.MidiFile — processed copy (original untouched)
        """
        pipeline_start = time.time()
        tpb = midi_file.ticks_per_beat

        self.ctx.report.input_metrics = {
            'total_notes': count_notes_midi(midi_file),
            'tracks': len(midi_file.tracks),
            'ticks_per_beat': tpb,
        }
        self.ctx.report.track_names = [
            get_track_info(t, i, tpb)['name']
            for i, t in enumerate(midi_file.tracks)
        ]

        output = mido.MidiFile(type=midi_file.type, ticks_per_beat=tpb)

        time_sig = (4, 4)
        if midi_file.tracks:
            time_sig = get_time_signature(midi_file.tracks[0])
        bar_ticks = calculate_bar_ticks(tpb, time_sig)
        processing_start_tick = (self.start_bar - 1) * bar_ticks

        tempo_dedup = TempoDeduplicator(self.config)

        for track_idx, track in enumerate(midi_file.tracks):
            track_info = get_track_info(track, track_idx, tpb)
            deduped = tempo_dedup.process(copy.deepcopy(track), tpb)

            if not track_info['has_notes']:
                output.tracks.append(deduped)
                continue

            track_config = self._get_track_config(track_idx, track_info)
            processed = self._process_track(
                deduped, tpb, track_config, processing_start_tick, time_sig
            )
            processed = self._strip_conductor_meta(processed)
            output.tracks.append(processed)

        # Telemetry for tempo dedup (aggregate across all tracks)
        input_tempo = sum(1 for t in midi_file.tracks for m in t if m.type == 'set_tempo')
        output_tempo = sum(1 for t in output.tracks for m in t if m.type == 'set_tempo')
        step = self.ctx.begin_step('TempoDeduplicator',
                                   self.config.get('tempo_deduplicator', {}).get('enabled', True),
                                   count_notes_midi(midi_file))
        step.tempo_events_removed = max(0, input_tempo - output_tempo)
        self.ctx.end_step(count_notes_midi(output))

        # File-level merge
        pre_merge_notes = count_notes_midi(output)
        merge_step = self.ctx.begin_step('MergeTracksToSingleTrack',
                                         self.config.get('merge_tracks', {}).get('enabled', False),
                                         pre_merge_notes)
        output = MergeTracksToSingleTrack(self.config).process(output)
        merge_step.tracks_merged = len(output.tracks) == 1
        self.ctx.end_step(count_notes_midi(output))

        self.ctx.report.output_metrics = {
            'total_notes': count_notes_midi(output),
            'tracks': len(output.tracks),
        }
        self.ctx.finalize(pipeline_start)

        return output

    def _process_track(self, track, tpb, config, start_tick, time_sig):
        """Apply all processors to a single track.

        If start_tick > 0, only process notes after that tick position,
        leaving earlier notes untouched.
        """
        if start_tick > 0:
            before, after = self._split_track_at_tick(track, start_tick)
            processed_after = self._apply_processors(after, tpb, config, time_sig)
            return self._merge_track_halves(before, processed_after, start_tick)
        else:
            return self._apply_processors(track, tpb, config, time_sig)

    def _apply_processors(self, track, tpb, config, time_sig=(4, 4)):
        """Apply all processing steps in order, with telemetry."""
        result = track

        steps = [
            ('PitchCluster', lambda r: PitchClusterProcessor(config).process(r, tpb),
             config.get('pitch_cluster', {}).get('enabled', True)),
            ('VoiceMerger', lambda r: VoiceMerger(config).process(r, tpb),
             config.get('merge_voices', True)),
            ('CCFilter', lambda r: CCFilter(config).process(r, tpb),
             config.get('remove_cc', True)),
            ('TripletRemover', lambda r: TripletRemover(config).process(r, tpb),
             config.get('remove_triplets', True)),
            ('Quantizer', lambda r: Quantizer(config).process(r, tpb, time_sig=time_sig),
             config.get('quantize', True)),
            ('NoiseFilter', lambda r: NoiseFilter(config).process(r, tpb),
             config.get('filter_noise', True)),
            ('SamePitchOverlapResolver', lambda r: SamePitchOverlapResolver(config).process(r, tpb),
             config.get('same_pitch_overlap_resolver', {}).get('enabled', True)),
        ]

        for name, fn, enabled in steps:
            nc_before = count_notes(result)
            self.ctx.begin_step(name, enabled, nc_before)
            result = fn(result)
            self.ctx.end_step(count_notes(result))

        if config.get('merge_voices', True):
            nc = count_notes(result)
            self.ctx.begin_step('FinalChordAlignment', True, nc)
            result = self._final_chord_alignment(result)
            self.ctx.end_step(count_notes(result))

        return result

    def _final_chord_alignment(self, track):
        """Post-processing: align chord durations one last time.

        After all processors have run, some chords may have acquired different
        durations per note (e.g. quantizer snapping differently, triplet converter
        changing some notes). This final pass ensures Guitar Pro sees one voice.
        """
        note_pairs = extract_note_pairs(track)
        non_notes = extract_non_note_messages(track)
        if not note_pairs:
            return track

        by_onset = defaultdict(list)
        for note in note_pairs:
            by_onset[note['onset']].append(note)

        result = []
        for onset, notes in sorted(by_onset.items()):
            if len(notes) > 1:
                durations = [n['offset'] - n['onset'] for n in notes]
                if len(set(durations)) > 1:
                    shortest = min(durations)
                    for note in notes:
                        note['offset'] = note['onset'] + shortest
            result.extend(notes)

        result.sort(key=lambda n: (n['onset'], n['pitch']))
        return rebuild_track_from_pairs(result, non_notes)

    def _strip_conductor_meta(self, track):
        """Remove set_tempo and time_signature events from a data track.

        In Type 1 MIDI, these should only exist in Track 0 (conductor track).
        When present in data tracks, Guitar Pro adds spurious tempo markings
        like ♩=87, ♩=91 to the notation.
        """
        new_track = mido.MidiTrack()
        abs_time = 0
        prev_abs = 0

        for msg in track:
            abs_time += msg.time
            if msg.is_meta and msg.type in self.CONDUCTOR_ONLY_META:
                # Skip this message, accumulate its time into the next message
                continue
            delta = max(0, int(round(abs_time - prev_abs)))
            new_track.append(msg.copy(time=delta))
            prev_abs = abs_time

        # Ensure end_of_track exists
        if not new_track or new_track[-1].type != 'end_of_track':
            new_track.append(mido.MetaMessage('end_of_track', time=0))

        return new_track

    def _get_track_config(self, track_idx, track_info):
        """Build configuration for a specific track, merging global + per-track overrides."""
        config = dict(self.config)
        overrides = self.config.get('track_overrides', {})

        # Track overrides are keyed by track index (as string from JSON)
        track_key = str(track_idx)
        if track_key in overrides:
            config.update(overrides[track_key])

        return config

    def _split_track_at_tick(self, track, split_tick):
        """Split a track into two parts at a given absolute tick.

        Returns (before_track, after_track) as mido.MidiTrack objects.
        The 'before' part retains all messages up to split_tick.
        The 'after' part contains messages from split_tick onward.
        Meta messages (track_name, etc.) are duplicated in both.
        """
        before = mido.MidiTrack()
        after = mido.MidiTrack()

        abs_time = 0
        before_time = 0
        after_time = 0

        for msg in track:
            abs_time += msg.time

            if msg.is_meta and msg.type in ('track_name', 'instrument_name',
                                             'key_signature'):
                # Duplicate these meta messages in both halves
                # NOTE: Do NOT duplicate set_tempo/time_signature — those stay in Track 0 only
                before.append(msg.copy(time=max(0, abs_time - before_time)))
                before_time = abs_time
                after.append(msg.copy(time=0))
                continue

            if abs_time < split_tick:
                delta = max(0, abs_time - before_time)
                before.append(msg.copy(time=delta))
                before_time = abs_time
            else:
                delta = max(0, abs_time - after_time - split_tick)
                after.append(msg.copy(time=max(0, int(round(delta)))))
                after_time = abs_time - split_tick

        return before, after

    def _merge_track_halves(self, before, after, split_tick):
        """Merge two track halves back together at the split point."""
        merged = mido.MidiTrack()

        # Add all 'before' messages
        for msg in before:
            merged.append(msg)

        # Calculate current absolute time in 'before'
        before_abs = sum(msg.time for msg in before)

        # Add gap if needed
        gap = split_tick - before_abs
        first_after = True

        # Track which meta types we've already seen from 'before'
        seen_meta = set()
        for msg in before:
            if msg.is_meta:
                seen_meta.add(msg.type)

        for msg in after:
            # Skip duplicate meta messages that were already in 'before'
            if msg.is_meta and msg.type in seen_meta and msg.time == 0:
                seen_meta.discard(msg.type)  # Only skip first occurrence
                continue

            if first_after and gap > 0:
                merged.append(msg.copy(time=max(0, int(round(gap + msg.time)))))
                first_after = False
            else:
                merged.append(msg)

        # Ensure end_of_track
        if not merged or merged[-1].type != 'end_of_track':
            merged.append(mido.MetaMessage('end_of_track', time=0))

        return merged
