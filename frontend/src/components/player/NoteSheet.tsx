import { useState, useEffect, useCallback } from 'react';
import * as Icons from '../common/Icons';
import { fetchTrackNotation } from '../../api/client';

interface NoteEvent {
  keys: string[];
  duration: string;
  is_rest: boolean;
  tab?: { string: number; fret: number }[];
}

interface Measure {
  notes: NoteEvent[];
}

interface NotationData {
  clef: string;
  time_signature: [number, number];
  measures: Measure[];
  show_tab: boolean;
}

interface NoteSheetProps {
  hasFile: boolean;
  hasProcessed: boolean;
  source: 'original' | 'processed';
  trackIndex: number | null;
}

const DURATION_SYMBOLS: Record<string, string> = {
  w: '𝅝', h: '𝅗𝅥', q: '♩', '8': '♪', '16': '𝅘𝅥𝅯', '32': '𝅘𝅥𝅰',
  wr: '𝄻', hr: '𝄼', qr: '𝄽', '8r': '𝄾', '16r': '𝄿',
};

function formatKey(key: string): string {
  return key.replace('/', '').toUpperCase();
}

function durationLabel(dur: string): string {
  return DURATION_SYMBOLS[dur] || dur;
}

export default function NoteSheet({ hasFile, hasProcessed, source, trackIndex }: NoteSheetProps) {
  const [notation, setNotation] = useState<NotationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const loadNotation = useCallback(async () => {
    if (trackIndex === null) return;
    setLoading(true);
    setError('');
    try {
      const s = source === 'processed' && !hasProcessed ? 'original' : source;
      const data = (await fetchTrackNotation(trackIndex, s, 64)) as NotationData;
      setNotation(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load notation');
    } finally {
      setLoading(false);
    }
  }, [trackIndex, source, hasProcessed]);

  useEffect(() => {
    if (hasFile && trackIndex !== null) {
      loadNotation();
    } else {
      setNotation(null);
    }
  }, [hasFile, trackIndex, loadNotation]);

  if (!hasFile) return null;

  if (trackIndex === null) {
    return (
      <div className="text-[10px] text-muted-foreground text-center py-4">
        Select a track above to view notation
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-4 gap-2 text-muted-foreground text-xs">
        <Icons.Loader size={14} /> Loading notation...
      </div>
    );
  }

  if (error) {
    return <div className="text-destructive text-xs text-center py-4">{error}</div>;
  }

  if (!notation || notation.measures.length === 0) {
    return (
      <div className="text-muted-foreground text-xs text-center py-4">
        No notation data available
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
        <span>Clef: {notation.clef}</span>
        <span>Time: {notation.time_signature[0]}/{notation.time_signature[1]}</span>
        <span>{notation.measures.length} measures</span>
        {notation.show_tab && <span className="text-primary">TAB</span>}
      </div>

      <div className="grid grid-cols-4 gap-1.5 max-h-[300px] overflow-y-auto pr-1">
        {notation.measures.map((measure, mIdx) => (
          <div
            key={mIdx}
            className="bg-surface rounded border border-border p-1.5 min-h-[48px]"
          >
            <div className="text-[8px] text-muted-foreground mb-1">
              Bar {mIdx + 1}
            </div>
            <div className="flex flex-wrap gap-0.5">
              {measure.notes.map((note, nIdx) => (
                <span
                  key={nIdx}
                  className={`text-[9px] px-1 py-0.5 rounded ${
                    note.is_rest
                      ? 'bg-surface-2/50 text-muted-foreground/60'
                      : 'bg-surface-2 text-foreground'
                  }`}
                >
                  {note.is_rest
                    ? durationLabel(note.duration)
                    : `${note.keys.map(formatKey).join('+')} ${durationLabel(note.duration)}`}
                  {!note.is_rest && note.tab && note.tab.length > 0 && (
                    <span className="text-primary/70 ml-0.5">
                      [{note.tab.map((t) => `${t.string}:${t.fret}`).join(',')}]
                    </span>
                  )}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
