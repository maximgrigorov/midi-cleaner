import type { LlmDecision } from '../../api/client';

interface LlmDecisionCardProps {
  decision: LlmDecision;
}

export default function LlmDecisionCard({ decision }: LlmDecisionCardProps) {
  return (
    <div className="bg-surface rounded-md border border-border p-3 space-y-1.5 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground">
          Call #{decision.call_number}
        </span>
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded ${
            decision.parsed_ok
              ? 'bg-green-900/30 text-success'
              : 'bg-red-900/30 text-destructive'
          }`}
        >
          {decision.parsed_ok ? 'Parsed OK' : 'Parse Error'}
        </span>
      </div>
      {decision.suggested_changes &&
        Object.keys(decision.suggested_changes).length > 0 && (
          <div className="flex flex-wrap gap-1">
            {Object.entries(decision.suggested_changes).map(([k, v]) => (
              <span
                key={k}
                className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 text-muted-foreground"
              >
                {k}: {String(v)}
              </span>
            ))}
          </div>
        )}
      {decision.error && (
        <p className="text-[11px] text-destructive">{decision.error}</p>
      )}
    </div>
  );
}
