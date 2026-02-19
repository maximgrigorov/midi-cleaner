export interface MidiConfig {
  tempo_deduplicator: { enabled: boolean };
  merge_voices: boolean;
  remove_overlaps: boolean;
  same_pitch_overlap_resolver: { enabled: boolean };
  filter_noise: boolean;
  min_duration_ticks: number;
  min_velocity: number;
  remove_triplets: boolean;
  quantize: boolean;
  quantize_grid: string;
  triplet_tolerance: number;
  remove_cc: boolean;
  cc_numbers: number[];
  pitch_cluster: {
    enabled: boolean;
    time_window_ticks: number;
    pitch_threshold: number;
  };
  start_bar: number;
  merge_tracks: { enabled: boolean; include_cc: boolean };
  track_overrides: Record<string, Record<string, unknown>>;
  llm: {
    enabled: boolean;
    api_base: string;
    model: string;
    max_calls: number;
    max_tokens: number;
  };
  [key: string]: unknown;
}

export const DEFAULT_CONFIG: MidiConfig = {
  tempo_deduplicator: { enabled: true },
  merge_voices: true,
  remove_overlaps: true,
  same_pitch_overlap_resolver: { enabled: true },
  filter_noise: true,
  min_duration_ticks: 120,
  min_velocity: 20,
  remove_triplets: true,
  quantize: true,
  quantize_grid: 'eighth',
  triplet_tolerance: 0.15,
  remove_cc: true,
  cc_numbers: [64, 68],
  pitch_cluster: { enabled: true, time_window_ticks: 20, pitch_threshold: 1 },
  start_bar: 1,
  merge_tracks: { enabled: false, include_cc: false },
  track_overrides: {},
  llm: {
    enabled: true,
    api_base: 'http://host.containers.internal:4000',
    model: 'gpt-4o-mini',
    max_calls: 3,
    max_tokens: 600,
  },
};
