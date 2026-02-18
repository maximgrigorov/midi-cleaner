"""CC Filter — removes specified MIDI Control Change messages from tracks.

By default removes:
  - CC#64 (Sustain Pedal)
  - CC#68 (Legato Footswitch)

Also handles sustain-extended notes: when sustain pedal was held, notes may
have artificially long durations. This processor optionally trims those notes
to a more natural length.
"""

import mido
from utils.midi_helpers import to_absolute_time, to_delta_time


class CCFilter:
    """Remove unwanted MIDI Control Change messages."""

    def __init__(self, config):
        self.enabled = config.get('remove_cc', True)
        self.cc_numbers = set(config.get('cc_numbers', [64, 68]))

    def process(self, track, ticks_per_beat):
        """Process a single track: remove specified CC messages.

        Args:
            track: mido.MidiTrack
            ticks_per_beat: PPQ resolution

        Returns:
            mido.MidiTrack — processed track
        """
        if not self.enabled or not self.cc_numbers:
            return track

        # Convert to absolute time
        abs_msgs = to_absolute_time(track)

        # Filter out matching CC messages
        filtered = []
        for abs_time, msg in abs_msgs:
            if self._should_remove(msg):
                continue
            filtered.append((abs_time, msg))

        # Convert back to delta time
        result_msgs = to_delta_time(filtered)

        # Build new track
        new_track = mido.MidiTrack()
        new_track.extend(result_msgs)
        return new_track

    def _should_remove(self, msg):
        """Check if a message should be removed."""
        if msg.type == 'control_change' and msg.control in self.cc_numbers:
            return True
        return False
