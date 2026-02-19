import type { ReactNode } from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon?: ReactNode;
  color?: 'default' | 'success' | 'warning' | 'destructive';
  barPercent?: number;
}

const colorMap: Record<string, string> = {
  default: 'bg-primary',
  success: 'bg-success',
  warning: 'bg-warning',
  destructive: 'bg-destructive',
};

export default function MetricCard({
  label,
  value,
  subValue,
  icon,
  color = 'default',
  barPercent,
}: MetricCardProps) {
  return (
    <div className="bg-surface rounded-lg border border-border p-4 space-y-3 animate-fade-in">
      <div className="flex items-center justify-between">
        <span className="text-xs text-muted-foreground">{label}</span>
        <div className="text-muted-foreground">{icon}</div>
      </div>
      <div>
        <div className="text-2xl font-semibold text-foreground">{value}</div>
        {subValue && (
          <div className="text-xs text-muted-foreground mt-0.5">
            {subValue}
          </div>
        )}
      </div>
      {barPercent !== undefined && (
        <div className="h-1.5 rounded-full bg-surface-2 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-700 ${colorMap[color]}`}
            style={{
              width: `${Math.min(100, Math.max(0, barPercent))}%`,
            }}
          />
        </div>
      )}
    </div>
  );
}
