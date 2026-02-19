import { useState } from 'react';
import * as Icons from '../common/Icons';
import EmptyState from '../common/EmptyState';
import MetricCard from '../results/MetricCard';
import ProcessorRow from '../results/ProcessorRow';
import MetricsCharts from '../results/MetricsCharts';
import ComparisonTable from '../results/ComparisonTable';
import MidiPlayer from '../player/MidiPlayer';
import type { ProcessResult } from '../../api/client';
import { DEFAULT_CONFIG, type MidiConfig } from '../../config';

interface CenterPanelProps {
  result: ProcessResult | null;
  config: MidiConfig;
  hasFile: boolean;
  hasProcessed: boolean;
}

type Tab = 'overview' | 'log' | 'player' | 'metrics' | 'comparison';

export default function CenterPanel({
  result,
  config,
  hasFile,
  hasProcessed,
}: CenterPanelProps) {
  const [tab, setTab] = useState<Tab>('overview');

  const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <Icons.FileMusic size={14} /> },
    { id: 'log', label: 'Processing Log', icon: <Icons.List size={14} /> },
    { id: 'player', label: 'Player', icon: <Icons.Play size={14} /> },
    { id: 'metrics', label: 'Metrics', icon: <Icons.BarChart size={14} /> },
    {
      id: 'comparison',
      label: 'Comparison',
      icon: <Icons.GitCompare size={14} />,
    },
  ];

  if (!result) {
    return (
      <div className="flex-1 bg-background flex flex-col">
        <div className="border-b border-border px-6 pt-4">
          <div className="flex bg-surface-2 rounded-md h-8 p-0.5 w-fit">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-1.5 text-xs h-7 px-3 rounded-sm transition ${
                  tab === t.id
                    ? 'bg-surface text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {t.icon} {t.label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex-1 overflow-y-auto">
          {tab === 'player' ? (
            <div className="p-6">
              <MidiPlayer hasFile={hasFile} hasProcessed={hasProcessed} />
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <EmptyState
                title="Ready to process"
                description="Load a MIDI file and click Process to begin."
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  const totalRemoved = result
    ? result.report.steps.reduce((a, s) => a + s.notes_removed, 0)
    : 0;
  const track = result?.tracks.find((t) => t.note_count > 0);
  const notesBefore = track ? track.note_count + totalRemoved : 1000;
  const notesAfter = track ? track.note_count : notesBefore - totalRemoved;
  const improvementPct = Math.round(
    ((notesBefore - notesAfter) / notesBefore) * 100
  );
  const overlapsRemoved =
    result?.report.steps.find((s) =>
      s.name.toLowerCase().includes('overlap')
    )?.notes_removed || 0;
  const cleanlinessScore = (1 - totalRemoved / notesBefore) * 100;

  return (
    <div className="flex-1 bg-background overflow-y-auto flex flex-col">
      <div className="border-b border-border px-6 pt-4">
        <div className="flex bg-surface-2 rounded-md h-8 p-0.5 w-fit">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 text-xs h-7 px-3 rounded-sm transition ${
                tab === t.id
                  ? 'bg-surface text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {tab === 'overview' && result && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Notes"
              value={`${notesBefore} → ${notesAfter}`}
              icon={<Icons.FileMusic size={16} />}
              color="success"
              barPercent={(notesAfter / notesBefore) * 100}
            />
            <MetricCard
              label="Overlaps Removed"
              value={overlapsRemoved}
              icon={<Icons.GitCompare size={16} />}
              color={overlapsRemoved > 50 ? 'warning' : 'success'}
              barPercent={Math.min(100, overlapsRemoved)}
            />
            <MetricCard
              label="Cleanliness"
              value={`${cleanlinessScore.toFixed(0)}%`}
              icon={<Icons.BarChart size={16} />}
              color={cleanlinessScore > 80 ? 'success' : 'warning'}
              barPercent={cleanlinessScore}
            />
            <MetricCard
              label="Improvement"
              value={`${improvementPct}%`}
              subValue={`${totalRemoved} notes cleaned`}
              icon={<Icons.BarChart size={16} />}
              color={improvementPct > 10 ? 'success' : 'default'}
              barPercent={improvementPct}
            />
          </div>
        )}
        {tab === 'log' && result && (
          <div className="space-y-2">
            {result.report.steps.map((step, i) => (
              <ProcessorRow key={i} step={step} index={i} />
            ))}
          </div>
        )}
        {tab === 'player' && (
          <MidiPlayer hasFile={hasFile} hasProcessed={hasProcessed} />
        )}
        {tab === 'metrics' && result && <MetricsCharts result={result} />}
        {tab === 'comparison' && (
          <ComparisonTable
            before={DEFAULT_CONFIG as unknown as Record<string, unknown>}
            after={config as unknown as Record<string, unknown>}
          />
        )}
      </div>
    </div>
  );
}
