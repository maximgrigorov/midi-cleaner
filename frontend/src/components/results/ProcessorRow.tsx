import { useState } from 'react';
import * as Icons from '../common/Icons';
import type { ProcessorStep } from '../../api/client';

function deriveEffect(step: ProcessorStep): 'improvement' | 'neutral' | 'skipped' {
  if (!step.enabled) return 'skipped';
  if (step.notes_removed > 0 || step.overlaps_resolved > 0 || step.clusters_merged > 0 || step.tempo_events_removed > 0 || step.tracks_merged)
    return 'improvement';
  return 'neutral';
}

function buildDetails(step: ProcessorStep): string {
  if (!step.enabled) return 'Skipped (disabled)';
  const parts: string[] = [];
  if (step.notes_removed > 0) parts.push(`${step.notes_removed} notes removed`);
  if (step.overlaps_resolved > 0) parts.push(`${step.overlaps_resolved} overlaps resolved`);
  if (step.clusters_merged > 0) parts.push(`${step.clusters_merged} clusters merged`);
  if (step.tempo_events_removed > 0) parts.push(`${step.tempo_events_removed} tempo events removed`);
  if (step.tracks_merged) parts.push('Tracks merged');
  if (step.warnings?.length) parts.push(`Warnings: ${step.warnings.join(', ')}`);
  parts.push(`${step.input_note_count} → ${step.output_note_count} notes`);
  return parts.join(' · ');
}

const borderColors: Record<string, string> = {
  improvement: 'border-l-success',
  neutral: 'border-l-border',
  skipped: 'border-l-muted-foreground',
};

const badgeColors: Record<string, string> = {
  improvement: 'bg-green-900/30 text-success',
  neutral: 'bg-surface-2 text-muted-foreground',
  skipped: 'bg-surface-2 text-muted-foreground/50',
};

interface ProcessorRowProps {
  step: ProcessorStep;
  index: number;
}

export default function ProcessorRow({ step, index }: ProcessorRowProps) {
  const [expanded, setExpanded] = useState(false);
  const effect = deriveEffect(step);
  const details = buildDetails(step);

  return (
    <div
      className={`border-l-2 bg-surface rounded-md border border-border animate-fade-in ${borderColors[effect]}`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 px-3 py-2.5 text-left"
      >
        <span className="text-xs font-medium text-foreground flex-1">
          {step.name}
        </span>
        <span className="text-[10px] font-mono text-muted-foreground">
          {step.duration_ms}ms
        </span>
        {step.notes_removed > 0 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-900/20 text-success">
            -{step.notes_removed}
          </span>
        )}
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded ${badgeColors[effect]}`}
        >
          {effect}
        </span>
        <span
          style={{
            transform: expanded ? 'rotate(180deg)' : '',
            transition: 'transform 0.2s',
            display: 'inline-block',
          }}
        >
          <Icons.ChevronDown size={12} />
        </span>
      </button>
      {expanded && (
        <div className="px-3 pb-2.5 text-xs text-muted-foreground border-t border-border pt-2">
          {details}
        </div>
      )}
    </div>
  );
}
