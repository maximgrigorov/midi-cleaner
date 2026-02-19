import InfoTooltip from '../common/Tooltip';

interface SliderRowProps {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
  step: number;
  tooltip?: string;
  disabled?: boolean;
  format?: (v: number) => string;
}

export default function SliderRow({
  label,
  value,
  onChange,
  min,
  max,
  step,
  tooltip,
  disabled,
  format,
}: SliderRowProps) {
  return (
    <div className="py-1.5 space-y-1.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-foreground">{label}</span>
          {tooltip && <InfoTooltip text={tooltip} />}
        </div>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-2 text-muted-foreground">
          {format ? format(value) : value}
        </span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
      />
    </div>
  );
}
