import { useState } from 'react';
import * as Icons from '../common/Icons';
import EmptyState from '../common/EmptyState';
import { downloadMidi, downloadReport, type ProcessResult } from '../../api/client';
import type { MidiConfig } from '../../config';

interface RightPanelProps {
  result: ProcessResult | null;
  config: MidiConfig;
  toast: (t: { title: string; description?: string; variant?: string }) => void;
}

export default function RightPanel({ result, config, toast }: RightPanelProps) {
  const [showConfig, setShowConfig] = useState(false);
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  if (!result) {
    return (
      <div className="w-[260px] shrink-0 border-l border-border bg-surface flex flex-col">
        <EmptyState
          title="No results yet"
          description="Process a MIDI file to see download options."
        />
      </div>
    );
  }

  const handleDownloadMidi = async () => {
    setDownloading('midi');
    try {
      const blob = await downloadMidi();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'cleaned.mid';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast({ title: 'Download failed', variant: 'destructive' });
    } finally {
      setDownloading(null);
    }
  };

  const handleDownloadReport = async () => {
    setDownloading('report');
    try {
      const blob = await downloadReport();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'report.json';
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast({ title: 'Download failed', variant: 'destructive' });
    } finally {
      setDownloading(null);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(JSON.stringify(config, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({ title: 'Copy failed', variant: 'destructive' });
    }
  };

  return (
    <div className="w-[260px] shrink-0 border-l border-border bg-surface flex flex-col overflow-hidden">
      <div className="p-4 space-y-2 border-b border-border">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
          Export
        </h3>
        <button
          onClick={handleDownloadMidi}
          disabled={downloading === 'midi'}
          className="w-full h-9 text-xs font-medium rounded-md bg-primary text-primary-foreground hover:opacity-90 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          <Icons.Download size={14} /> Download Clean MIDI
        </button>
        <button
          onClick={handleDownloadReport}
          disabled={downloading === 'report'}
          className="w-full h-8 text-xs rounded-md border border-border bg-surface-2 hover:bg-muted text-foreground transition flex items-center justify-center gap-1.5 disabled:opacity-50"
        >
          <Icons.Download size={14} /> Download Report JSON
        </button>
        <button
          onClick={handleCopy}
          className="w-full h-8 text-xs rounded-md border border-border bg-surface-2 hover:bg-muted text-foreground transition flex items-center justify-center gap-1.5"
        >
          {copied ? (
            <>
              <Icons.Check size={14} className="text-success" /> Copied!
            </>
          ) : (
            <>
              <Icons.Copy size={14} /> Copy Parameters
            </>
          )}
        </button>
      </div>
      <div className="p-4">
        <button
          type="button"
          onClick={() => setShowConfig(!showConfig)}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <Icons.Code size={14} /> {showConfig ? 'Hide' : 'Show'} Raw Config
        </button>
        {showConfig && (
          <pre className="mt-3 p-3 rounded-md bg-background border border-border text-[10px] font-mono text-muted-foreground overflow-auto max-h-[400px] leading-relaxed animate-fade-in">
            {JSON.stringify(config, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
}
