import * as Icons from '../common/Icons';
import Panel from '../common/Panel';
import EmptyState from '../common/EmptyState';
import ToggleRow from '../controls/ToggleRow';
import SliderRow from '../controls/SliderRow';
import SelectRow from '../controls/SelectRow';
import { TOOLTIPS } from '../../tooltips';
import type { UploadResponse, TrackInfo } from '../../api/client';
import type { MidiConfig } from '../../config';

function midiNoteToName(note: number): string {
  const names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
  return `${names[note % 12]}${Math.floor(note / 12) - 1}`;
}

const TYPE_BADGES: Record<string, string> = {
  guitar: 'bg-blue-900/30 text-blue-400',
  bass: 'bg-green-900/30 text-green-400',
  vocal: 'bg-purple-900/30 text-purple-400',
  strings: 'bg-yellow-900/30 text-yellow-400',
  drums: 'bg-red-900/30 text-red-400',
  unknown: 'bg-surface-2 text-muted-foreground',
};

interface LeftPanelProps {
  config: MidiConfig;
  updateConfig: (patch: Partial<MidiConfig>) => void;
  updateNestedConfig: (key: string, patch: Record<string, unknown>) => void;
  uploadData: UploadResponse | null;
  showAdvanced: boolean;
  isProcessing: boolean;
  onProcess: () => void;
  selectedTrack: number | null;
  onSelectTrack: (idx: number | null) => void;
}

export default function LeftPanel({
  config,
  updateConfig,
  updateNestedConfig,
  uploadData,
  showAdvanced,
  isProcessing,
  onProcess,
  selectedTrack,
  onSelectTrack,
}: LeftPanelProps) {
  const disabled = !uploadData;

  if (!uploadData) {
    return (
      <div className="w-[280px] shrink-0 border-r border-border bg-surface flex flex-col">
        <EmptyState title="No file loaded" description="Upload a MIDI file to begin." />
      </div>
    );
  }

  const overrides = (config.track_overrides || {}) as Record<string, Record<string, unknown>>;
  const currentOverrides = selectedTrack !== null
    ? (overrides[String(selectedTrack)] || {})
    : {};

  const setTrackOverride = (param: string, value: unknown) => {
    if (selectedTrack === null) return;
    const key = String(selectedTrack);
    const existing = overrides[key] || {};
    updateConfig({
      track_overrides: {
        ...overrides,
        [key]: { ...existing, [param]: value },
      },
    } as Partial<MidiConfig>);
  };

  return (
    <div className="w-[280px] shrink-0 border-r border-border bg-surface flex flex-col overflow-hidden">
      <div className="px-4 py-3 border-b border-border">
        <div className="text-xs font-medium text-foreground truncate">
          {uploadData.filename}
        </div>
        <div className="text-[10px] text-muted-foreground mt-0.5">
          {uploadData.num_tracks} tracks · {uploadData.ticks_per_beat} TPB · Type{' '}
          {uploadData.type}
        </div>
      </div>

      {/* Track Overview */}
      <div className="border-b border-border">
        <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Tracks
        </div>
        <div className="px-2 pb-2 space-y-0.5 max-h-[160px] overflow-y-auto">
          {uploadData.tracks.filter((t: TrackInfo) => t.has_notes).map((track: TrackInfo) => (
            <button
              key={track.index}
              type="button"
              onClick={() =>
                onSelectTrack(selectedTrack === track.index ? null : track.index)
              }
              className={`w-full flex items-center gap-2 px-2 py-1.5 rounded text-left transition ${
                selectedTrack === track.index
                  ? 'bg-primary/15 border border-primary/30'
                  : 'hover:bg-surface-2 border border-transparent'
              }`}
            >
              <div className="flex-1 min-w-0">
                <div className="text-[11px] text-foreground truncate">
                  {track.name || `Track ${track.index}`}
                </div>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span
                    className={`text-[9px] px-1 py-0.5 rounded ${TYPE_BADGES[track.track_type] || TYPE_BADGES.unknown}`}
                  >
                    {track.track_type}
                  </span>
                  {track.note_count > 0 && (
                    <span className="text-[9px] text-muted-foreground">
                      {track.note_count} notes
                    </span>
                  )}
                  {track.note_range[0] > 0 && (
                    <span className="text-[9px] text-muted-foreground">
                      {midiNoteToName(track.note_range[0])}–
                      {midiNoteToName(track.note_range[1])}
                    </span>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <Panel title="Cleaning">
          <ToggleRow
            label="Deduplicate Tempo"
            checked={(config.tempo_deduplicator as { enabled: boolean }).enabled}
            onChange={(v) =>
              updateNestedConfig('tempo_deduplicator', { enabled: v })
            }
            tooltip={TOOLTIPS.tempo_deduplicator}
            disabled={disabled}
          />
          <ToggleRow
            label="Merge Voices"
            checked={config.merge_voices as boolean}
            onChange={(v) => updateConfig({ merge_voices: v })}
            tooltip={TOOLTIPS.merge_voices}
            disabled={disabled}
          />
          <ToggleRow
            label="Remove Overlaps"
            checked={config.remove_overlaps as boolean}
            onChange={(v) => updateConfig({ remove_overlaps: v })}
            tooltip={TOOLTIPS.remove_overlaps}
            disabled={disabled}
          />
          <ToggleRow
            label="Same-pitch Resolver"
            checked={
              (config.same_pitch_overlap_resolver as { enabled: boolean }).enabled
            }
            onChange={(v) =>
              updateNestedConfig('same_pitch_overlap_resolver', { enabled: v })
            }
            tooltip={TOOLTIPS.same_pitch_overlap_resolver}
            disabled={disabled}
          />
          <ToggleRow
            label="Noise Filter"
            checked={config.filter_noise as boolean}
            onChange={(v) => updateConfig({ filter_noise: v })}
            tooltip={TOOLTIPS.filter_noise}
            disabled={disabled}
          />
          {config.filter_noise && (
            <>
              <SliderRow
                label="Min Duration"
                value={config.min_duration_ticks as number}
                onChange={(v) => updateConfig({ min_duration_ticks: v })}
                min={30}
                max={480}
                step={10}
                tooltip={TOOLTIPS.min_duration_ticks}
                disabled={disabled}
                format={(v) => `${v} ticks`}
              />
              <SliderRow
                label="Min Velocity"
                value={config.min_velocity as number}
                onChange={(v) => updateConfig({ min_velocity: v })}
                min={0}
                max={127}
                step={1}
                tooltip={TOOLTIPS.min_velocity}
                disabled={disabled}
              />
            </>
          )}
        </Panel>

        <Panel title="Rhythm">
          <ToggleRow
            label="Remove Triplets"
            checked={config.remove_triplets as boolean}
            onChange={(v) => updateConfig({ remove_triplets: v })}
            tooltip={TOOLTIPS.remove_triplets}
            disabled={disabled}
          />
          <ToggleRow
            label="Quantize"
            checked={config.quantize as boolean}
            onChange={(v) => updateConfig({ quantize: v })}
            tooltip={TOOLTIPS.quantize}
            disabled={disabled}
          />
          {config.quantize && (
            <SelectRow
              label="Grid"
              value={config.quantize_grid as string}
              options={[
                { value: 'quarter', label: '¼' },
                { value: 'eighth', label: '⅛' },
                { value: 'sixteenth', label: '1/16' },
              ]}
              onChange={(v) => updateConfig({ quantize_grid: v })}
              tooltip={TOOLTIPS.quantize_grid}
              disabled={disabled}
            />
          )}
        </Panel>

        {showAdvanced && (
          <Panel title="Advanced" defaultOpen={true}>
            <SliderRow
              label="Triplet Tolerance"
              value={config.triplet_tolerance as number}
              onChange={(v) => updateConfig({ triplet_tolerance: v })}
              min={0.05}
              max={0.3}
              step={0.01}
              tooltip={TOOLTIPS.triplet_tolerance}
              disabled={disabled}
              format={(v) => v.toFixed(2)}
            />
            <ToggleRow
              label="Remove CC Messages"
              checked={config.remove_cc as boolean}
              onChange={(v) => updateConfig({ remove_cc: v })}
              tooltip={TOOLTIPS.remove_cc}
              disabled={disabled}
            />
            {config.remove_cc && (
              <div className="pl-1 space-y-1">
                <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(config.cc_numbers as number[]).includes(64)}
                    onChange={(e) =>
                      updateConfig({
                        cc_numbers: e.target.checked
                          ? [...(config.cc_numbers as number[]), 64]
                          : (config.cc_numbers as number[]).filter(
                              (n) => n !== 64
                            ),
                      })
                    }
                    className="accent-primary"
                  />
                  CC#64 Sustain
                </label>
                <label className="flex items-center gap-2 text-xs text-muted-foreground cursor-pointer">
                  <input
                    type="checkbox"
                    checked={(config.cc_numbers as number[]).includes(68)}
                    onChange={(e) =>
                      updateConfig({
                        cc_numbers: e.target.checked
                          ? [...(config.cc_numbers as number[]), 68]
                          : (config.cc_numbers as number[]).filter(
                              (n) => n !== 68
                            ),
                      })
                    }
                    className="accent-primary"
                  />
                  CC#68 Legato
                </label>
              </div>
            )}
            <ToggleRow
              label="Pitch Cluster"
              checked={
                (config.pitch_cluster as { enabled: boolean }).enabled
              }
              onChange={(v) =>
                updateNestedConfig('pitch_cluster', { enabled: v })
              }
              tooltip={TOOLTIPS.pitch_cluster}
              disabled={disabled}
            />
            {(config.pitch_cluster as { enabled: boolean }).enabled && (
              <>
                <SliderRow
                  label="Time Window"
                  value={
                    (
                      config.pitch_cluster as {
                        time_window_ticks: number;
                      }
                    ).time_window_ticks
                  }
                  onChange={(v) =>
                    updateNestedConfig('pitch_cluster', {
                      time_window_ticks: v,
                    })
                  }
                  min={5}
                  max={100}
                  step={1}
                  tooltip={TOOLTIPS.time_window_ticks}
                  disabled={disabled}
                  format={(v) => `${v} ticks`}
                />
                <SliderRow
                  label="Pitch Threshold"
                  value={
                    (config.pitch_cluster as { pitch_threshold: number })
                      .pitch_threshold
                  }
                  onChange={(v) =>
                    updateNestedConfig('pitch_cluster', {
                      pitch_threshold: v,
                    })
                  }
                  min={0}
                  max={3}
                  step={1}
                  tooltip={TOOLTIPS.pitch_threshold}
                  disabled={disabled}
                  format={(v) => `${v} st`}
                />
              </>
            )}
            <div className="py-1.5 space-y-1.5">
              <span className="text-xs text-foreground">Start from Bar</span>
              <input
                type="number"
                value={config.start_bar as number}
                onChange={(e) =>
                  updateConfig({
                    start_bar: Math.max(1, parseInt(e.target.value) || 1),
                  })
                }
                min={1}
                max={999}
                disabled={disabled}
                className="w-full h-7 text-xs bg-surface-2 border border-border rounded-md px-2 text-foreground outline-none"
              />
            </div>
            <ToggleRow
              label="Merge All Tracks"
              checked={
                (config.merge_tracks as { enabled: boolean }).enabled
              }
              onChange={(v) =>
                updateNestedConfig('merge_tracks', { enabled: v })
              }
              tooltip={TOOLTIPS.merge_tracks}
              disabled={disabled}
            />
            <ToggleRow
              label="LLM Guidance"
              checked={(config.llm as { enabled: boolean }).enabled}
              onChange={(v) => updateNestedConfig('llm', { enabled: v })}
              tooltip={TOOLTIPS.llm}
              disabled={disabled}
            />
            {(config.llm as { enabled: boolean }).enabled && (
              <>
                <div className="py-1.5 space-y-1.5">
                  <span className="text-xs text-foreground">Model</span>
                  <input
                    value={(config.llm as { model: string }).model}
                    onChange={(e) =>
                      updateNestedConfig('llm', { model: e.target.value })
                    }
                    disabled={disabled}
                    className="w-full h-7 text-xs font-mono bg-surface-2 border border-border rounded-md px-2 text-foreground outline-none"
                  />
                </div>
                <div className="py-1.5 space-y-1.5">
                  <span className="text-xs text-foreground">API Base</span>
                  <input
                    value={
                      (config.llm as { api_base: string }).api_base || ''
                    }
                    onChange={(e) =>
                      updateNestedConfig('llm', { api_base: e.target.value })
                    }
                    disabled={disabled}
                    placeholder="http://host.containers.internal:4000"
                    className="w-full h-7 text-xs font-mono bg-surface-2 border border-border rounded-md px-2 text-foreground outline-none"
                  />
                </div>
                <SliderRow
                  label="Max Calls"
                  value={(config.llm as { max_calls: number }).max_calls}
                  onChange={(v) =>
                    updateNestedConfig('llm', { max_calls: v })
                  }
                  min={1}
                  max={10}
                  step={1}
                  disabled={disabled}
                />
              </>
            )}
          </Panel>
        )}

        {/* Per-Track Overrides */}
        {showAdvanced && selectedTrack !== null && (
          <Panel title={`Track ${selectedTrack} Override`} defaultOpen={true}>
            <SliderRow
              label="Min Duration"
              value={(currentOverrides.min_duration_ticks as number) ?? (config.min_duration_ticks as number)}
              onChange={(v) => setTrackOverride('min_duration_ticks', v)}
              min={30}
              max={480}
              step={10}
              tooltip="Override min duration for this track only"
              format={(v) => `${v} ticks`}
            />
            <SliderRow
              label="Min Velocity"
              value={(currentOverrides.min_velocity as number) ?? (config.min_velocity as number)}
              onChange={(v) => setTrackOverride('min_velocity', v)}
              min={0}
              max={127}
              step={1}
              tooltip="Override min velocity for this track only"
            />
            <ToggleRow
              label="Remove Overlaps"
              checked={(currentOverrides.remove_overlaps as boolean) ?? (config.remove_overlaps as boolean)}
              onChange={(v) => setTrackOverride('remove_overlaps', v)}
              tooltip="Override overlap removal for this track"
            />
            <ToggleRow
              label="Merge Voices"
              checked={(currentOverrides.merge_voices as boolean) ?? (config.merge_voices as boolean)}
              onChange={(v) => setTrackOverride('merge_voices', v)}
              tooltip="Override voice merging for this track"
            />
          </Panel>
        )}
      </div>

      <div className="p-4 border-t border-border">
        <button
          onClick={onProcess}
          disabled={disabled || isProcessing}
          className="w-full h-9 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:opacity-90 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          {isProcessing ? (
            <>
              <Icons.Loader size={14} /> Processing…
            </>
          ) : (
            'Process & Clean'
          )}
        </button>
      </div>
    </div>
  );
}
