import { useState, useEffect, useRef, useCallback } from 'react';
import * as Icons from '../common/Icons';
import { fetchTrackNotation } from '../../api/client';
import {
  Renderer,
  Stave,
  StaveNote,
  Formatter,
  Voice,
  type RenderContext,
} from 'vexflow';

interface NoteEvent {
  keys: string[];
  duration: string;
  is_rest: boolean;
  tab?: { str: number; fret: number }[];
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

const STAVE_WIDTH = 300;
const STAVE_HEIGHT = 140;
const MEASURES_PER_LINE = 4;
const LEFT_MARGIN = 10;

export default function NoteSheet({
  hasFile,
  hasProcessed,
  source,
  trackIndex,
}: NoteSheetProps) {
  const [notation, setNotation] = useState<NotationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const loadNotation = useCallback(async () => {
    if (trackIndex === null) return;
    setLoading(true);
    setError('');
    try {
      const s = source === 'processed' && !hasProcessed ? 'original' : source;
      const data = (await fetchTrackNotation(trackIndex, s, 32)) as NotationData;
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

  useEffect(() => {
    if (!notation || !containerRef.current) return;
    const container = containerRef.current;
    container.innerHTML = '';

    const { measures, clef, time_signature } = notation;
    if (measures.length === 0) return;

    const lines = Math.ceil(measures.length / MEASURES_PER_LINE);
    const totalWidth = MEASURES_PER_LINE * STAVE_WIDTH + LEFT_MARGIN * 2;
    const totalHeight = lines * STAVE_HEIGHT + 40;

    const renderer = new Renderer(container, Renderer.Backends.SVG);
    renderer.resize(totalWidth, totalHeight);
    const context = renderer.getContext() as RenderContext;
    context.setFont('Arial', 10);

    for (let i = 0; i < measures.length; i++) {
      const lineIdx = Math.floor(i / MEASURES_PER_LINE);
      const colIdx = i % MEASURES_PER_LINE;
      const x = LEFT_MARGIN + colIdx * STAVE_WIDTH;
      const y = lineIdx * STAVE_HEIGHT + 10;

      const isFirstInLine = colIdx === 0;

      const stave = new Stave(x, y, STAVE_WIDTH);
      if (isFirstInLine) {
        stave.addClef(clef);
        if (lineIdx === 0) {
          stave.addTimeSignature(`${time_signature[0]}/${time_signature[1]}`);
        }
      }
      stave.setContext(context);
      stave.draw();

      const measure = measures[i];
      if (!measure.notes || measure.notes.length === 0) continue;

      try {
        const vfNotes = measure.notes
          .map((n) => {
            try {
              const keys = n.keys && n.keys.length > 0 ? n.keys : ['b/4'];
              let dur = n.duration || 'q';
              if (n.is_rest && !dur.endsWith('r')) dur += 'r';
              // VexFlow valid durations
              const baseDur = dur.replace('r', '').replace('d', '');
              const validDurs = ['1', '2', '4', '8', '16', '32', 'w', 'h', 'q'];
              if (!validDurs.includes(baseDur)) dur = n.is_rest ? 'qr' : 'q';
              return new StaveNote({
                keys,
                duration: dur,
                clef,
              });
            } catch {
              return null;
            }
          })
          .filter((n): n is StaveNote => n !== null);

        if (vfNotes.length === 0) continue;

        const voice = new Voice({
          numBeats: time_signature[0],
          beatValue: time_signature[1],
        }).setStrict(false);
        voice.addTickables(vfNotes);

        new Formatter()
          .joinVoices([voice])
          .format([voice], STAVE_WIDTH - (isFirstInLine ? 80 : 20));

        voice.draw(context, stave);
      } catch {
        // skip measures that fail to render
      }
    }
  }, [notation]);

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
    return (
      <div className="text-destructive text-xs text-center py-4">{error}</div>
    );
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
        <span>
          Time: {notation.time_signature[0]}/{notation.time_signature[1]}
        </span>
        <span>{notation.measures.length} measures</span>
        {notation.show_tab && <span className="text-primary">TAB</span>}
      </div>
      <div
        ref={containerRef}
        className="bg-white rounded-lg overflow-x-auto"
        style={{ minHeight: '160px' }}
      />
    </div>
  );
}
