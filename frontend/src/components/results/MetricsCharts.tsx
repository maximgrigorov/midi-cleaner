import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import type { ProcessResult } from '../../api/client';

function midiNoteToName(note: number): string {
  const names = [
    'C','C#','D','D#','E','F','F#','G','G#','A','A#','B',
  ];
  return `${names[note % 12]}${Math.floor(note / 12) - 1}`;
}

const COLORS = {
  primary: 'hsl(239,84%,67%)',
  success: 'hsl(142,71%,45%)',
  muted: 'hsl(240,5%,20%)',
  warning: 'hsl(38,92%,50%)',
};

interface MetricsChartsProps {
  result: ProcessResult;
}

export default function MetricsCharts({ result }: MetricsChartsProps) {
  const totalRemoved = result.report.steps.reduce(
    (a, s) => a + s.notes_removed,
    0
  );
  const track = result.tracks.find((t) => t.note_count > 0);
  const notesBefore = track ? track.note_count + totalRemoved : 1000;
  const notesAfter = track ? track.note_count : notesBefore - totalRemoved;
  const removedPercent = Math.round((totalRemoved / notesBefore) * 100);
  const noteRange = track?.note_range || [40, 84];
  const polyphonyData = [
    { name: 'Before', value: notesBefore },
    { name: 'After', value: notesAfter },
  ];
  const donutData = [
    { name: 'Removed', value: totalRemoved },
    { name: 'Kept', value: notesAfter },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-surface rounded-lg border border-border p-4">
        <h4 className="text-xs font-medium text-muted-foreground mb-3">
          Note Count (Before vs After)
        </h4>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={polyphonyData} layout="vertical" barGap={4}>
            <XAxis type="number" hide />
            <YAxis
              type="category"
              dataKey="name"
              width={50}
              tick={{ fontSize: 11, fill: 'hsl(240,5%,50%)' }}
              axisLine={false}
              tickLine={false}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              <Cell fill={COLORS.muted} />
              <Cell fill={COLORS.primary} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="bg-surface rounded-lg border border-border p-4">
        <h4 className="text-xs font-medium text-muted-foreground mb-3">
          Notes Removed
        </h4>
        <div className="flex items-center gap-6">
          <ResponsiveContainer width={100} height={100}>
            <PieChart>
              <Pie
                data={donutData}
                innerRadius={30}
                outerRadius={45}
                dataKey="value"
                startAngle={90}
                endAngle={-270}
              >
                <Cell fill={COLORS.warning} />
                <Cell fill={COLORS.muted} />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div>
            <div className="text-2xl font-semibold text-foreground">
              {removedPercent}%
            </div>
            <div className="text-xs text-muted-foreground">
              {totalRemoved} of {notesBefore} notes
            </div>
          </div>
        </div>
      </div>
      <div className="bg-surface rounded-lg border border-border p-4">
        <h4 className="text-xs font-medium text-muted-foreground mb-3">
          Pitch Range
        </h4>
        <div className="flex items-center justify-between">
          <div className="text-center">
            <div className="text-lg font-semibold text-foreground">
              {midiNoteToName(noteRange[0])}
            </div>
            <div className="text-[10px] text-muted-foreground">
              MIDI {noteRange[0]}
            </div>
          </div>
          <div className="flex-1 mx-4 h-2 rounded-full bg-surface-2 relative overflow-hidden">
            <div
              className="absolute h-full rounded-full bg-gradient-to-r from-primary to-success"
              style={{
                left: `${(noteRange[0] / 127) * 100}%`,
                right: `${100 - (noteRange[1] / 127) * 100}%`,
              }}
            />
          </div>
          <div className="text-center">
            <div className="text-lg font-semibold text-foreground">
              {midiNoteToName(noteRange[1])}
            </div>
            <div className="text-[10px] text-muted-foreground">
              MIDI {noteRange[1]}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
