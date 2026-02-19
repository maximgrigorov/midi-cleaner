import { useState, useCallback, useEffect, useRef } from 'react';
import Header from './components/layout/Header';
import LeftPanel from './components/layout/LeftPanel';
import CenterPanel from './components/layout/CenterPanel';
import RightPanel from './components/layout/RightPanel';
import OptimizePanel from './components/optimize/OptimizePanel';
import { DEFAULT_CONFIG, type MidiConfig } from './config';
import {
  uploadFile,
  fetchPresets,
  fetchPresetConfig,
  suggestPreset,
  processFile,
  startOptimize,
  fetchOptimizeStatus,
  applyOptimize,
  type UploadResponse,
  type ProcessResult,
  type PresetItem,
  type OptimizeStatus,
} from './api/client';

interface Toast {
  id: number;
  title: string;
  description?: string;
  variant?: string;
}

let toastIdCounter = 0;

function ToastContainer({ toasts }: { toasts: Toast[] }) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast-item ${t.variant === 'destructive' ? 'destructive' : ''}`}
        >
          <div className="font-medium">{t.title}</div>
          {t.description && (
            <div className="text-muted-foreground mt-1">{t.description}</div>
          )}
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [config, setConfig] = useState<MidiConfig>({ ...DEFAULT_CONFIG });
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [processResult, setProcessResult] = useState<ProcessResult | null>(null);
  const [presets, setPresets] = useState<PresetItem[]>([]);
  const [selectedPreset, setSelectedPreset] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);

  const [isOptimizing, setIsOptimizing] = useState(false);
  const [showOptimize, setShowOptimize] = useState(false);
  const [isOptConfiguring, setIsOptConfiguring] = useState(false);
  const [optMaxTrials, setOptMaxTrials] = useState(40);
  const [optLlmConfig, setOptLlmConfig] = useState({ ...DEFAULT_CONFIG.llm });
  const [optStatus, setOptStatus] = useState<OptimizeStatus | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [toasts, setToasts] = useState<Toast[]>([]);
  const toast = useCallback(
    (t: { title: string; description?: string; variant?: string }) => {
      const id = ++toastIdCounter;
      setToasts((prev) => [...prev, { ...t, id }]);
      setTimeout(
        () => setToasts((prev) => prev.filter((x) => x.id !== id)),
        5000
      );
    },
    []
  );

  const updateConfig = useCallback(
    (patch: Partial<MidiConfig>) => setConfig((prev) => ({ ...prev, ...patch })),
    []
  );
  const updateNestedConfig = useCallback(
    (key: string, patch: Record<string, unknown>) =>
      setConfig((prev) => ({
        ...prev,
        [key]:
          typeof prev[key] === 'object' && prev[key] !== null
            ? { ...(prev[key] as Record<string, unknown>), ...patch }
            : patch,
      })),
    []
  );

  useEffect(() => {
    fetchPresets()
      .then(setPresets)
      .catch(() =>
        toast({ title: 'Failed to load presets', variant: 'destructive' })
      );
  }, [toast]);

  const selectPreset = useCallback(
    async (id: string) => {
      setSelectedPreset(id);
      if (!id) return;
      try {
        const pc = await fetchPresetConfig(id);
        setConfig((prev) => ({ ...prev, ...(pc as Partial<MidiConfig>) }));
      } catch {
        toast({ title: 'Failed to load preset', variant: 'destructive' });
      }
    },
    [toast]
  );

  const handleUpload = useCallback(
    async (file: File) => {
      setIsUploading(true);
      try {
        const data = await uploadFile(file);
        setUploadData(data);
        setProcessResult(null);
        setSelectedTrack(null);
        try {
          const s = await suggestPreset();
          setSelectedPreset(s.preset_id);
          setConfig((prev) => ({
            ...prev,
            ...(s.config as Partial<MidiConfig>),
          }));
        } catch {
          // suggestion is optional
        }
        toast({
          title: 'File loaded',
          description: `${data.filename} — ${data.num_tracks} tracks, ${data.ticks_per_beat} TPB`,
        });
      } catch {
        toast({ title: 'Upload failed', variant: 'destructive' });
      } finally {
        setIsUploading(false);
      }
    },
    [toast]
  );

  const handleProcess = useCallback(async () => {
    setIsProcessing(true);
    try {
      const result = await processFile(
        config as unknown as Record<string, unknown>
      );
      setProcessResult(result);
      toast({
        title: 'Processing complete',
        description: `${result.report.steps.reduce((a, s) => a + s.notes_removed, 0)} notes cleaned`,
      });
    } catch {
      toast({ title: 'Processing failed', variant: 'destructive' });
    } finally {
      setIsProcessing(false);
    }
  }, [config, toast]);

  const handleShowOptimize = useCallback(() => {
    setShowOptimize(true);
    setIsOptConfiguring(true);
    setOptStatus(null);
    setOptLlmConfig({ ...config.llm });
  }, [config.llm]);

  const handleRunOptimize = useCallback(async () => {
    setIsOptConfiguring(false);
    setIsOptimizing(true);
    setOptStatus(null);
    try {
      await startOptimize(optMaxTrials, optLlmConfig as unknown as Record<string, unknown>);
      pollRef.current = setInterval(async () => {
        try {
          const s = await fetchOptimizeStatus();
          setOptStatus(s);
          if (s.status === 'done' || s.status === 'error') {
            clearInterval(pollRef.current!);
            pollRef.current = null;
            setIsOptimizing(false);
            if (s.status === 'error') {
              toast({
                title: 'Optimization error',
                description: s.error,
                variant: 'destructive',
              });
            }
          }
        } catch {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setIsOptimizing(false);
          toast({ title: 'Polling error', variant: 'destructive' });
        }
      }, 1500);
    } catch {
      setIsOptimizing(false);
      toast({
        title: 'Failed to start optimization',
        variant: 'destructive',
      });
    }
  }, [optMaxTrials, optLlmConfig, toast]);

  const handleApplyOptimize = useCallback(async () => {
    try {
      const result = await applyOptimize();
      toast({
        title: 'Settings applied',
        description: `Best score: ${result.best_score.toFixed(2)}`,
      });
      setShowOptimize(false);
      if (result.best_params) {
        updateConfig(result.best_params as Partial<MidiConfig>);
      }
    } catch {
      toast({ title: 'Apply failed', variant: 'destructive' });
    }
  }, [toast, updateConfig]);

  const handleDismissOptimize = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
    setIsOptimizing(false);
    setIsOptConfiguring(false);
    setShowOptimize(false);
    setOptStatus(null);
  }, []);

  const handleOptLlmConfigChange = useCallback(
    (key: string, value: unknown) => {
      setOptLlmConfig((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  // Drag & drop
  const [isDragging, setIsDragging] = useState(false);
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);
  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (
        file &&
        (file.name.endsWith('.mid') || file.name.endsWith('.midi'))
      ) {
        handleUpload(file);
      } else if (file) {
        toast({
          title: 'Wrong file type',
          description: 'Please drop a .mid or .midi file',
          variant: 'destructive',
        });
      }
    },
    [handleUpload, toast]
  );

  return (
    <div
      className="h-screen flex flex-col bg-background overflow-hidden relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {isDragging && (
        <div
          className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none"
          style={{
            background: 'rgba(99,102,241,0.12)',
            border: '2px dashed #6366f1',
            borderRadius: '12px',
          }}
        >
          <div className="text-center">
            <div style={{ fontSize: '48px' }}>🎵</div>
            <div className="text-lg font-semibold text-primary mt-2">
              Drop MIDI file here
            </div>
          </div>
        </div>
      )}

      <Header
        presets={presets}
        selectedPreset={selectedPreset}
        onSelectPreset={selectPreset}
        onUpload={handleUpload}
        isUploading={isUploading}
        showAdvanced={showAdvanced}
        onToggleAdvanced={setShowAdvanced}
        onOptimize={handleShowOptimize}
        hasFile={!!uploadData}
      />

      {showOptimize && (
        <OptimizePanel
          status={optStatus}
          isOptimizing={isOptimizing}
          isConfiguring={isOptConfiguring}
          maxTrials={optMaxTrials}
          onMaxTrialsChange={setOptMaxTrials}
          llmConfig={optLlmConfig}
          onLlmConfigChange={handleOptLlmConfigChange}
          onStart={handleRunOptimize}
          onApply={handleApplyOptimize}
          onDismiss={handleDismissOptimize}
        />
      )}

      <div className="flex flex-1 overflow-hidden">
        <LeftPanel
          config={config}
          updateConfig={updateConfig}
          updateNestedConfig={updateNestedConfig}
          uploadData={uploadData}
          showAdvanced={showAdvanced}
          isProcessing={isProcessing}
          onProcess={handleProcess}
          selectedTrack={selectedTrack}
          onSelectTrack={setSelectedTrack}
        />
        <CenterPanel
          result={processResult}
          config={config}
          hasFile={!!uploadData}
          hasProcessed={!!processResult}
        />
        <RightPanel result={processResult} config={config} toast={toast} />
      </div>

      <ToastContainer toasts={toasts} />
    </div>
  );
}
