import { useRef } from 'react';
import * as Icons from '../common/Icons';
import InfoTooltip from '../common/Tooltip';
import { Toggle } from '../controls/ToggleRow';
import type { PresetItem } from '../../api/client';
import { TOOLTIPS } from '../../tooltips';

interface HeaderProps {
  presets: PresetItem[];
  selectedPreset: string;
  onSelectPreset: (id: string) => void;
  onUpload: (file: File) => void;
  isUploading: boolean;
  showAdvanced: boolean;
  onToggleAdvanced: (v: boolean) => void;
  onOptimize?: () => void;
  onReset: () => void;
  onHistory: () => void;
  hasFile: boolean;
}

export default function Header({
  presets,
  selectedPreset,
  onSelectPreset,
  onUpload,
  isUploading,
  showAdvanced,
  onToggleAdvanced,
  onOptimize,
  onReset,
  onHistory,
  hasFile,
}: HeaderProps) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <header className="h-14 border-b border-border bg-surface flex items-center px-4 gap-4 shrink-0">
      <div className="flex items-center gap-2 min-w-[180px]">
        <Icons.Music size={20} className="text-primary" />
        <span className="text-sm font-semibold text-foreground tracking-tight">
          MIDI Cleaner
        </span>
      </div>

      <div className="flex-1 flex justify-center">
        <select
          value={selectedPreset}
          onChange={(e) => onSelectPreset(e.target.value)}
          disabled={!hasFile}
          className="w-[280px] h-8 text-xs bg-surface-2 border border-border rounded-md px-2 text-foreground disabled:opacity-50 outline-none"
        >
          <option value="">Select a preset…</option>
          {presets.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label} — {p.description}
            </option>
          ))}
        </select>
      </div>

      <div className="flex items-center gap-3 min-w-[420px] justify-end">
        <input
          ref={fileRef}
          type="file"
          accept=".mid,.midi"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUpload(f);
            e.target.value = '';
          }}
        />
        <button
          onClick={() => fileRef.current?.click()}
          disabled={isUploading}
          className="flex items-center gap-1.5 px-3 h-8 text-xs rounded-md border border-border bg-surface-2 hover:bg-muted text-foreground transition disabled:opacity-50"
        >
          {isUploading ? (
            <Icons.Loader size={14} />
          ) : (
            <Icons.Upload size={14} />
          )}
          Load MIDI
        </button>
        <button
          onClick={onOptimize}
          disabled={!hasFile || !onOptimize}
          className="flex items-center gap-1.5 px-3 h-8 text-xs rounded-md border border-border bg-surface-2 hover:bg-muted text-foreground transition disabled:opacity-50"
        >
          <Icons.Sparkles size={14} />
          Auto Optimize
          <InfoTooltip text={TOOLTIPS.auto_optimize} />
        </button>
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <Icons.Settings size={14} className="text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Advanced</span>
          <Toggle checked={showAdvanced} onChange={onToggleAdvanced} />
        </div>
        <button
          onClick={onHistory}
          className="flex items-center gap-1.5 px-2 h-8 text-xs text-muted-foreground hover:text-foreground transition border-l border-border pl-3"
          title="Session history"
        >
          <Icons.Clock size={14} />
          History
        </button>
        <button
          onClick={onReset}
          className="flex items-center gap-1.5 px-2 h-8 text-xs text-muted-foreground hover:text-foreground transition"
          title="Reset all settings"
        >
          <Icons.X size={14} />
          Reset
        </button>
        <a
          href="/docs/"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 px-2 h-8 text-xs text-muted-foreground hover:text-foreground transition border-l border-border pl-3"
        >
          <Icons.ExternalLink size={14} />
          Docs
        </a>
      </div>
    </header>
  );
}
