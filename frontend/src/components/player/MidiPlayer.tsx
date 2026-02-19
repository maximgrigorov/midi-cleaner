import { useState, useEffect, useRef, useCallback } from 'react';
import * as Icons from '../common/Icons';
import {
  fetchAllTracksPlayback,
  type AllTracksPlayback,
  type PlaybackNote,
} from '../../api/client';

const TRACK_COLORS = [
  'hsl(234,89%,73%)',
  'hsl(142,71%,45%)',
  'hsl(38,92%,50%)',
  'hsl(0,84%,60%)',
  'hsl(261,72%,65%)',
  'hsl(180,60%,50%)',
];

function midiToFreq(note: number): number {
  return 440 * Math.pow(2, (note - 69) / 12);
}

interface MidiPlayerProps {
  hasFile: boolean;
  hasProcessed: boolean;
}

export default function MidiPlayer({ hasFile, hasProcessed }: MidiPlayerProps) {
  const [source, setSource] = useState<'original' | 'processed'>('original');
  const [playbackData, setPlaybackData] = useState<AllTracksPlayback | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [selectedTrack, setSelectedTrack] = useState<number | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const scheduledRef = useRef<OscillatorNode[]>([]);
  const animFrameRef = useRef<number>(0);
  const playStartWallRef = useRef(0);
  const playStartOffsetRef = useRef(0);

  const loadPlayback = useCallback(async (src: 'original' | 'processed') => {
    setLoading(true);
    setError('');
    try {
      const data = await fetchAllTracksPlayback(src);
      setPlaybackData(data);
      setCurrentTime(0);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load playback');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (hasFile) {
      loadPlayback(source);
    }
  }, [hasFile, source, loadPlayback]);

  useEffect(() => {
    if (source === 'processed' && !hasProcessed) {
      setSource('original');
    }
  }, [hasProcessed, source]);

  const getVisibleNotes = useCallback(
    (trackFilter: number | null) => {
      if (!playbackData) return [];
      const tracks =
        trackFilter !== null
          ? playbackData.tracks.filter((t) => t.index === trackFilter)
          : playbackData.tracks;

      const allNotes: (PlaybackNote & { color: string })[] = [];
      tracks.forEach((track) => {
        const color =
          TRACK_COLORS[
            playbackData.tracks.indexOf(track) % TRACK_COLORS.length
          ];
        track.notes.forEach((n) => allNotes.push({ ...n, color }));
      });
      return allNotes;
    },
    [playbackData]
  );

  const drawPianoRoll = useCallback(
    (time: number) => {
      const canvas = canvasRef.current;
      if (!canvas || !playbackData) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
      const w = rect.width;
      const h = rect.height;

      ctx.fillStyle = 'hsl(0,0%,9%)';
      ctx.fillRect(0, 0, w, h);

      const allNotes = getVisibleNotes(selectedTrack);
      if (allNotes.length === 0) {
        ctx.fillStyle = 'hsl(0,0%,40%)';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No notes to display', w / 2, h / 2);
        return;
      }

      const minPitch = Math.max(0, Math.min(...allNotes.map((n) => n.pitch)) - 2);
      const maxPitch = Math.min(127, Math.max(...allNotes.map((n) => n.pitch)) + 2);
      const pitchRange = maxPitch - minPitch || 1;

      const duration = playbackData.duration || 10;
      const viewWindow = Math.min(duration, 10);
      const viewStart = Math.max(0, time - viewWindow * 0.3);

      // Grid
      ctx.strokeStyle = 'hsl(240,5%,15%)';
      ctx.lineWidth = 0.5;
      for (let p = minPitch; p <= maxPitch; p++) {
        const y = h - ((p - minPitch) / pitchRange) * h;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }

      // Notes
      for (const note of allNotes) {
        const x = ((note.time - viewStart) / viewWindow) * w;
        const noteW = (note.duration / viewWindow) * w;
        const y = h - ((note.pitch - minPitch) / pitchRange) * h - h / pitchRange;
        const noteH = Math.max(2, h / pitchRange - 1);

        if (x + noteW < 0 || x > w) continue;

        const alpha = note.velocity / 127;
        ctx.globalAlpha = 0.3 + alpha * 0.7;
        ctx.fillStyle = note.color;
        ctx.beginPath();
        ctx.roundRect(x, y, Math.max(2, noteW), noteH, 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;

      // Playhead
      const playheadX = ((time - viewStart) / viewWindow) * w;
      ctx.strokeStyle = 'hsl(0,84%,60%)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, h);
      ctx.stroke();

      // Time marker
      ctx.fillStyle = 'hsl(0,0%,60%)';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(`${time.toFixed(1)}s / ${duration.toFixed(1)}s`, 4, 12);
    },
    [playbackData, selectedTrack, getVisibleNotes]
  );

  useEffect(() => {
    if (playbackData && !playing) {
      drawPianoRoll(currentTime);
    }
  }, [playbackData, currentTime, playing, drawPianoRoll]);

  const stopPlayback = useCallback(() => {
    setPlaying(false);
    cancelAnimationFrame(animFrameRef.current);
    scheduledRef.current.forEach((osc) => {
      try { osc.stop(); } catch { /* already stopped */ }
    });
    scheduledRef.current = [];
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
  }, []);

  const startPlayback = useCallback(() => {
    if (!playbackData) return;

    const audioCtx = new AudioContext();
    audioCtxRef.current = audioCtx;

    const startOffset = currentTime;
    const now = audioCtx.currentTime;

    playStartWallRef.current = now;
    playStartOffsetRef.current = startOffset;

    const tracks =
      selectedTrack !== null
        ? playbackData.tracks.filter((t) => t.index === selectedTrack)
        : playbackData.tracks;

    const masterGain = audioCtx.createGain();
    masterGain.gain.value = 0.08;
    masterGain.connect(audioCtx.destination);

    tracks.forEach((track) => {
      track.notes.forEach((note) => {
        const noteEndTime = note.time + note.duration;
        if (noteEndTime < startOffset) return;

        const relativeStart = note.time - startOffset;
        const noteStart = now + Math.max(0, relativeStart);
        const noteEnd = now + (noteEndTime - startOffset);

        if (noteEnd <= now) return;

        const osc = audioCtx.createOscillator();
        const noteGain = audioCtx.createGain();
        osc.frequency.value = midiToFreq(note.pitch);
        osc.type = 'triangle';

        const attackTime = 0.01;
        const vol = note.velocity / 127;

        noteGain.gain.setValueAtTime(0, noteStart);
        noteGain.gain.linearRampToValueAtTime(vol, noteStart + attackTime);
        noteGain.gain.setValueAtTime(vol, Math.max(noteStart + attackTime, noteEnd - 0.02));
        noteGain.gain.linearRampToValueAtTime(0, noteEnd);

        osc.connect(noteGain);
        noteGain.connect(masterGain);

        osc.start(noteStart);
        osc.stop(noteEnd + 0.05);
        scheduledRef.current.push(osc);
      });
    });

    setPlaying(true);

    const animate = () => {
      if (!audioCtxRef.current) return;
      const elapsed = audioCtxRef.current.currentTime - playStartWallRef.current;
      const t = playStartOffsetRef.current + elapsed;
      setCurrentTime(t);
      drawPianoRoll(t);
      if (t < playbackData.duration) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        stopPlayback();
        setCurrentTime(0);
      }
    };
    animFrameRef.current = requestAnimationFrame(animate);
  }, [playbackData, currentTime, selectedTrack, drawPianoRoll, stopPlayback]);

  if (!hasFile) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground text-xs">
        Upload a file to see the player
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-muted-foreground text-xs">
        <Icons.Loader size={14} /> Loading playback data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-destructive text-xs">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-fade-in">
      <div className="flex items-center gap-3">
        <button
          onClick={playing ? stopPlayback : startPlayback}
          className="flex items-center gap-1.5 px-3 h-8 text-xs rounded-md bg-primary text-primary-foreground hover:opacity-90 transition"
        >
          {playing ? <Icons.Pause size={14} /> : <Icons.Play size={14} />}
          {playing ? 'Stop' : 'Play'}
        </button>

        <div className="flex bg-surface-2 rounded-md h-7 p-0.5">
          <button
            onClick={() => setSource('original')}
            className={`px-2 text-[10px] rounded-sm font-medium transition ${source === 'original' ? 'bg-surface text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Original
          </button>
          <button
            onClick={() => { if (hasProcessed) setSource('processed'); }}
            disabled={!hasProcessed}
            className={`px-2 text-[10px] rounded-sm font-medium transition disabled:opacity-40 ${source === 'processed' ? 'bg-surface text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
          >
            Processed
          </button>
        </div>

        {playbackData && playbackData.tracks.length > 1 && (
          <select
            value={selectedTrack ?? 'all'}
            onChange={(e) =>
              setSelectedTrack(e.target.value === 'all' ? null : Number(e.target.value))
            }
            className="h-7 text-[10px] bg-surface-2 border border-border rounded-md px-2 text-foreground outline-none"
          >
            <option value="all">All Tracks</option>
            {playbackData.tracks.map((t) => (
              <option key={t.index} value={t.index}>
                {t.name || `Track ${t.index}`}
              </option>
            ))}
          </select>
        )}

        {playbackData && (
          <div className="text-[10px] text-muted-foreground ml-auto">
            {playbackData.bpm} BPM · {playbackData.duration.toFixed(1)}s
          </div>
        )}
      </div>

      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full cursor-pointer"
          style={{ height: '220px' }}
          onClick={(e) => {
            if (!playbackData || playing) return;
            const rect = canvasRef.current!.getBoundingClientRect();
            const pct = (e.clientX - rect.left) / rect.width;
            const viewWindow = Math.min(playbackData.duration, 10);
            const viewStart = Math.max(0, currentTime - viewWindow * 0.3);
            const newTime = viewStart + pct * viewWindow;
            setCurrentTime(Math.max(0, Math.min(playbackData.duration, newTime)));
          }}
        />
      </div>

      {/* Progress bar */}
      {playbackData && (
        <div
          className="h-1 rounded-full bg-surface-2 overflow-hidden cursor-pointer"
          onClick={(e) => {
            if (!playbackData || playing) return;
            const rect = e.currentTarget.getBoundingClientRect();
            const pct = (e.clientX - rect.left) / rect.width;
            setCurrentTime(Math.max(0, pct * playbackData.duration));
          }}
        >
          <div
            className="h-full rounded-full bg-primary transition-all duration-100"
            style={{ width: `${(currentTime / (playbackData.duration || 1)) * 100}%` }}
          />
        </div>
      )}

      {playbackData && (
        <div className="flex gap-2 flex-wrap">
          {playbackData.tracks.map((t, i) => (
            <span
              key={t.index}
              className="flex items-center gap-1 text-[10px] text-muted-foreground"
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: TRACK_COLORS[i % TRACK_COLORS.length] }}
              />
              {t.name || `Track ${t.index}`} ({t.track_type})
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
