// Typed API client — all fetch calls to the Flask backend

export interface TrackInfo {
  index: number;
  name: string;
  track_type: string;
  note_count: number;
  note_range: [number, number];
  has_notes: boolean;
  suggested_thresholds: Record<string, number>;
}

export interface UploadResponse {
  file_id: string;
  filename: string;
  type: number;
  ticks_per_beat: number;
  num_tracks: number;
  tracks: TrackInfo[];
}

export interface ProcessorStep {
  name: string;
  enabled: boolean;
  notes_removed: number;
  duration_ms: number;
  input_note_count: number;
  output_note_count: number;
  overlaps_resolved: number;
  clusters_merged: number;
  tempo_events_removed: number;
  tracks_merged: boolean;
  warnings: string[];
}

export interface ProcessingReport {
  preset_applied: string;
  steps: ProcessorStep[];
}

export interface ProcessResult {
  success: boolean;
  file_id: string;
  tracks: TrackInfo[];
  report: ProcessingReport;
}

export interface PresetItem {
  id: string;
  label: string;
  description: string;
  track_types: string[];
}

export interface SuggestPresetResponse {
  track_type: string;
  preset_id: string;
  config: Record<string, unknown>;
}

export interface LlmDecision {
  call_number: number;
  suggested_changes: Record<string, unknown>;
  parsed_ok: boolean;
  error?: string;
}

export interface TrialInfo {
  number: number;
  score: number;
  params: Record<string, unknown>;
  metrics?: Record<string, unknown>;
}

export interface OptimizeStatus {
  status: string;
  current_trial: number;
  total_trials: number;
  best_score: number | null;
  best_params: Record<string, unknown>;
  current_params: Record<string, unknown>;
  track_type: string;
  stop_reason: string;
  trials: TrialInfo[];
  llm_decisions?: LlmDecision[];
  best_config?: Record<string, unknown>;
  error?: string;
}

export interface ApplyOptimizeResponse {
  success: boolean;
  best_params: Record<string, unknown>;
  best_score: number;
}

export interface PlaybackNote {
  pitch: number;
  time: number;
  duration: number;
  velocity: number;
}

export interface PlaybackData {
  bpm: number;
  notes: PlaybackNote[];
}

export interface AllTracksPlayback {
  bpm: number;
  duration: number;
  tracks: {
    index: number;
    name: string;
    track_type: string;
    notes: PlaybackNote[];
  }[];
}

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, credentials: 'include' });
  if (!res.ok) {
    let msg = `API error ${res.status}`;
    try {
      const body = await res.json();
      if (body.error) msg = body.error;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(msg, res.status);
  }
  return res.json();
}

async function apiBlobFetch(path: string): Promise<Blob> {
  const res = await fetch(path, { credentials: 'include' });
  if (!res.ok) {
    let msg = `API error ${res.status}`;
    try {
      const body = await res.json();
      if (body.error) msg = body.error;
    } catch {
      // ignore
    }
    throw new ApiError(msg, res.status);
  }
  return res.blob();
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const fd = new FormData();
  fd.append('file', file);
  return apiFetch<UploadResponse>('/api/upload', { method: 'POST', body: fd });
}

export async function fetchPresets(): Promise<PresetItem[]> {
  const res = await apiFetch<{ presets: PresetItem[] }>('/api/presets');
  return res.presets;
}

export async function fetchPresetConfig(
  id: string
): Promise<Record<string, unknown>> {
  const res = await apiFetch<{ config: Record<string, unknown> }>(
    `/api/presets/${id}`
  );
  return res.config;
}

export async function suggestPreset(): Promise<SuggestPresetResponse> {
  return apiFetch<SuggestPresetResponse>('/api/presets/suggest');
}

export async function processFile(
  config: Record<string, unknown>
): Promise<ProcessResult> {
  return apiFetch<ProcessResult>('/api/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
}

export async function downloadMidi(): Promise<Blob> {
  return apiBlobFetch('/api/download');
}

export async function downloadReport(): Promise<Blob> {
  return apiBlobFetch('/api/report/download');
}

export async function startOptimize(
  maxTrials: number,
  llmConfig?: Record<string, unknown>
): Promise<void> {
  await apiFetch('/api/optimize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ max_trials: maxTrials, llm: llmConfig }),
  });
}

export async function fetchOptimizeStatus(): Promise<OptimizeStatus> {
  return apiFetch<OptimizeStatus>('/api/optimize/status');
}

export async function applyOptimize(): Promise<ApplyOptimizeResponse> {
  return apiFetch<ApplyOptimizeResponse>('/api/optimize/apply', {
    method: 'POST',
  });
}

export async function fetchTrackPlayback(
  trackIdx: number,
  source: 'original' | 'processed' = 'original'
): Promise<PlaybackData> {
  return apiFetch<PlaybackData>(
    `/api/track/${trackIdx}/playback?source=${source}`
  );
}

export async function fetchAllTracksPlayback(
  source: 'original' | 'processed' = 'original'
): Promise<AllTracksPlayback> {
  return apiFetch<AllTracksPlayback>(`/api/playback/all?source=${source}`);
}

// ── Session History ──

export interface SessionEntry {
  id: string;
  session_id: string;
  filename: string;
  timestamp: number;
  num_tracks: number;
  status: 'uploaded' | 'processed';
  notes_removed: number | null;
}

export interface RestoreSessionResponse extends UploadResponse {
  has_processed: boolean;
  config: Record<string, unknown> | null;
}

export async function fetchSessions(): Promise<SessionEntry[]> {
  const res = await apiFetch<{ sessions: SessionEntry[] }>('/api/sessions');
  return res.sessions;
}

export async function restoreSession(
  fileId: string
): Promise<RestoreSessionResponse> {
  return apiFetch<RestoreSessionResponse>(
    `/api/sessions/${fileId}/restore`,
    { method: 'POST' }
  );
}

export async function clearSessions(): Promise<{ removed: number }> {
  return apiFetch<{ success: boolean; removed: number }>('/api/sessions', {
    method: 'DELETE',
  });
}

export async function fetchTrackNotation(
  trackIdx: number,
  source: 'original' | 'processed' = 'original',
  measures: number = 64
): Promise<unknown> {
  return apiFetch(`/api/track/${trackIdx}/notation?source=${source}&measures=${measures}`);
}
