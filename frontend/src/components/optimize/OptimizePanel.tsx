import * as Icons from '../common/Icons';
import LlmDecisionCard from './LlmDecisionCard';
import SliderRow from '../controls/SliderRow';
import ToggleRow from '../controls/ToggleRow';
import type { OptimizeStatus } from '../../api/client';
import type { MidiConfig } from '../../config';

interface OptimizePanelProps {
  status: OptimizeStatus | null;
  isOptimizing: boolean;
  isConfiguring: boolean;
  maxTrials: number;
  onMaxTrialsChange: (v: number) => void;
  llmConfig: MidiConfig['llm'];
  onLlmConfigChange: (key: string, value: unknown) => void;
  onStart: () => void;
  onApply: () => void;
  onDismiss: () => void;
}

export default function OptimizePanel({
  status,
  isOptimizing,
  isConfiguring,
  maxTrials,
  onMaxTrialsChange,
  llmConfig,
  onLlmConfigChange,
  onStart,
  onApply,
  onDismiss,
}: OptimizePanelProps) {
  const progress = status
    ? (status.current_trial / status.total_trials) * 100
    : 0;
  const isDone = status?.status === 'done';

  return (
    <div className="bg-surface border-b border-border px-6 py-4 animate-fade-in">
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icons.Sparkles size={16} className="text-primary" />
            <h3 className="text-sm font-semibold text-foreground">
              {isDone
                ? 'Optimization Complete'
                : isOptimizing
                  ? 'Auto Optimization'
                  : 'Auto Optimize'}
            </h3>
            {isDone && <Icons.Check size={16} className="text-success" />}
          </div>
          <button
            onClick={onDismiss}
            className="p-1 text-muted-foreground hover:text-foreground rounded"
          >
            <Icons.X size={16} />
          </button>
        </div>

        {/* Configuration step — shown before optimization starts */}
        {isConfiguring && !isOptimizing && !isDone && (
          <div className="space-y-4">
            <SliderRow
              label="Max Trials"
              value={maxTrials}
              onChange={onMaxTrialsChange}
              min={5}
              max={100}
              step={5}
              tooltip="Maximum optimization iterations (1–100)"
            />
            <div className="bg-surface-2 rounded-lg border border-border p-3 space-y-3">
              <ToggleRow
                label="LLM Guidance"
                checked={llmConfig.enabled}
                onChange={(v) => onLlmConfigChange('enabled', v)}
                tooltip="Use GPT-4o-mini as strategy advisor when optimizer stalls"
              />
              {llmConfig.enabled && (
                <div className="space-y-2 pl-1">
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted-foreground">
                      Model
                    </span>
                    <input
                      value={llmConfig.model}
                      onChange={(e) =>
                        onLlmConfigChange('model', e.target.value)
                      }
                      className="w-full h-7 text-xs font-mono bg-background border border-border rounded-md px-2 text-foreground outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted-foreground">
                      API Base
                    </span>
                    <input
                      value={llmConfig.api_base || ''}
                      onChange={(e) =>
                        onLlmConfigChange('api_base', e.target.value)
                      }
                      placeholder="http://alma:4000 (litellm proxy)"
                      className="w-full h-7 text-xs font-mono bg-background border border-border rounded-md px-2 text-foreground outline-none"
                    />
                  </div>
                  <SliderRow
                    label="Max LLM Calls"
                    value={llmConfig.max_calls}
                    onChange={(v) => onLlmConfigChange('max_calls', v)}
                    min={1}
                    max={10}
                    step={1}
                  />
                </div>
              )}
            </div>
            <p className="text-[10px] text-muted-foreground">
              Auto-optimize searches for the best parameters automatically.
              Preset settings are ignored — the optimizer explores its own parameter space.
            </p>
            <button
              onClick={onStart}
              className="flex items-center gap-1.5 px-4 py-2 rounded-md text-xs font-medium bg-primary text-primary-foreground hover:opacity-90 transition"
            >
              <Icons.Sparkles size={14} />
              Start Optimization
            </button>
          </div>
        )}

        {/* Running state */}
        {isOptimizing && status && (
          <>
            <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
              <div
                className="h-full rounded-full bg-primary transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex items-center gap-4 text-xs text-muted-foreground">
              <span>
                Trial {status.current_trial} of {status.total_trials}
              </span>
              {status.best_score !== null && (
                <span>
                  Best score:{' '}
                  <span className="text-foreground font-medium">
                    {status.best_score.toFixed(2)}
                  </span>
                </span>
              )}
              {status.track_type && (
                <span>
                  Track type:{' '}
                  <span className="text-foreground font-medium">
                    {status.track_type}
                  </span>
                </span>
              )}
            </div>
            {status.current_params &&
              Object.keys(status.current_params).length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(status.current_params).map(([k, v]) => (
                    <span
                      key={k}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-surface-2 text-muted-foreground"
                    >
                      {k}: {String(v)}
                    </span>
                  ))}
                </div>
              )}
          </>
        )}

        {/* Done state */}
        {isDone && status && (
          <div className="space-y-3">
            <div className="flex items-center gap-6 text-sm">
              <div>
                <span className="text-muted-foreground">Score: </span>
                <span className="text-foreground font-semibold">
                  {status.best_score?.toFixed(2)}
                </span>
              </div>
              {status.stop_reason && (
                <div>
                  <span className="text-muted-foreground">Stopped: </span>
                  <span className="text-foreground">{status.stop_reason}</span>
                </div>
              )}
              {status.track_type && (
                <div>
                  <span className="text-muted-foreground">Track type: </span>
                  <span className="text-foreground">{status.track_type}</span>
                </div>
              )}
            </div>

            {status.best_params &&
              Object.keys(status.best_params).length > 0 && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-1.5">
                    Best Parameters
                  </h4>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(status.best_params).map(([k, v]) => (
                      <span
                        key={k}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary"
                      >
                        {k}: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

            {status.llm_decisions && status.llm_decisions.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-xs font-medium text-muted-foreground">
                  AI Decisions
                </h4>
                {status.llm_decisions.map((d, i) => (
                  <LlmDecisionCard key={i} decision={d} />
                ))}
              </div>
            )}

            <button
              onClick={onApply}
              className="px-4 py-2 rounded-md text-xs font-medium bg-primary text-primary-foreground hover:opacity-90 transition"
            >
              Apply These Settings
            </button>
          </div>
        )}

        {status?.status === 'error' && (
          <div className="text-destructive text-xs">
            Error: {status.error || 'Unknown error'}
          </div>
        )}
      </div>
    </div>
  );
}
