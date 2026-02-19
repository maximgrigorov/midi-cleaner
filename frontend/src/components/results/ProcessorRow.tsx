import { useState } from 'react';
import * as Icons from '../common/Icons';
import type { ProcessorStep } from '../../api/client';

const borderColors: Record<string, string> = {
  improvement: 'border-l-success',
  neutral: 'border-l-warning',
  destructive: 'border-l-destructive',
};

const badgeColors: Record<string, string> = {
  improvement: 'bg-green-900/30 text-success',
  neutral: 'bg-yellow-900/30 text-warning',
  destructive: 'bg-red-900/30 text-destructive',
};

interface ProcessorRowProps {
  step: ProcessorStep;
  index: number;
}

export default function ProcessorRow({ step, index }: ProcessorRowProps) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className={`border-l-2 bg-surface rounded-md border border-border animate-fade-in ${borderColors[step.effect]}`}
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
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 text-muted-foreground">
            -{step.notes_removed}
          </span>
        )}
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded ${badgeColors[step.effect]}`}
        >
          {step.effect}
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
          {step.details}
        </div>
      )}
    </div>
  );
}
