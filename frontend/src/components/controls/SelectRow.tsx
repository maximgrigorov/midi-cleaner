import InfoTooltip from '../common/Tooltip';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectRowProps {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (v: string) => void;
  tooltip?: string;
  disabled?: boolean;
}

export default function SelectRow({
  label,
  value,
  options,
  onChange,
  tooltip,
  disabled,
}: SelectRowProps) {
  return (
    <div className="py-1.5 space-y-1.5">
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-foreground">{label}</span>
        {tooltip && <InfoTooltip text={tooltip} />}
      </div>
      <div className="flex rounded-md bg-surface-2 p-0.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(opt.value)}
            className={`flex-1 rounded-sm px-2 py-1 text-[10px] font-medium transition-all duration-150 ${
              value === opt.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
