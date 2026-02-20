import { useState, useEffect, useCallback } from 'react';
import * as Icons from '../common/Icons';
import {
  fetchSessions,
  clearSessions,
  type SessionEntry,
} from '../../api/client';

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onRestore: (fileId: string) => void;
  currentFileId: string | null;
}

function formatDate(ts: number): string {
  const d = new Date(ts * 1000);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMin = Math.floor(diffMs / 60_000);

  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;

  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function HistoryPanel({
  isOpen,
  onClose,
  onRestore,
  currentFileId,
}: HistoryPanelProps) {
  const [sessions, setSessions] = useState<SessionEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchSessions();
      setSessions(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) load();
  }, [isOpen, load]);

  const handleClear = async () => {
    if (!confirm('Delete all history and uploaded files? This cannot be undone.')) return;
    setClearing(true);
    try {
      await clearSessions();
      setSessions([]);
    } catch {
      // ignore
    } finally {
      setClearing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-40 flex">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="relative ml-auto w-[360px] h-full bg-surface border-l border-border flex flex-col shadow-xl animate-fade-in">
        <div className="flex items-center justify-between px-4 h-12 border-b border-border shrink-0">
          <span className="text-sm font-semibold text-foreground">Session History</span>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition">
            <Icons.X size={16} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading && (
            <div className="flex items-center justify-center py-8 text-muted-foreground text-xs gap-2">
              <Icons.Loader size={14} /> Loading...
            </div>
          )}
          {!loading && sessions.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground text-xs">
              <Icons.FileMusic size={24} className="mb-2 opacity-40" />
              No sessions yet
            </div>
          )}
          {!loading &&
            sessions.map((s) => (
              <button
                key={`${s.id}-${s.timestamp}`}
                onClick={() => onRestore(s.id)}
                disabled={s.id === currentFileId}
                className={`w-full text-left px-4 py-3 border-b border-border transition ${
                  s.id === currentFileId
                    ? 'bg-primary/10 border-l-2 border-l-primary'
                    : 'hover:bg-surface-2'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-foreground truncate max-w-[200px]">
                    {s.filename}
                  </span>
                  <span className="text-[10px] text-muted-foreground shrink-0 ml-2">
                    {formatDate(s.timestamp)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded ${
                      s.status === 'processed'
                        ? 'bg-green-900/30 text-green-400'
                        : 'bg-surface-2 text-muted-foreground'
                    }`}
                  >
                    {s.status}
                  </span>
                  <span className="text-[10px] text-muted-foreground">
                    {s.num_tracks} track{s.num_tracks !== 1 ? 's' : ''}
                  </span>
                  {s.notes_removed != null && (
                    <span className="text-[10px] text-muted-foreground">
                      {s.notes_removed} notes removed
                    </span>
                  )}
                  {s.id === currentFileId && (
                    <span className="text-[9px] text-primary font-medium">current</span>
                  )}
                </div>
              </button>
            ))}
        </div>

        {sessions.length > 0 && (
          <div className="p-3 border-t border-border shrink-0">
            <button
              onClick={handleClear}
              disabled={clearing}
              className="w-full h-8 text-xs font-medium rounded-md bg-red-900/30 text-red-400 hover:bg-red-900/50 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              {clearing ? (
                <Icons.Loader size={14} />
              ) : (
                <Icons.Trash size={14} />
              )}
              Clear All History & Files
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
