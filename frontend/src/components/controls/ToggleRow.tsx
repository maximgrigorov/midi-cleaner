import InfoTooltip from '../common/Tooltip';

interface ToggleProps {
  checked: boolean;
  onChange: (v: boolean) => void;
  disabled?: boolean;
}

function Toggle({ checked, onChange, disabled }: ToggleProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`toggle-switch ${checked ? 'on' : 'off'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
    >
      <span className="knob" />
    </button>
  );
}

interface ToggleRowProps {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  tooltip?: string;
  disabled?: boolean;
}

export default function ToggleRow({
  label,
  checked,
  onChange,
  tooltip,
  disabled,
}: ToggleRowProps) {
  return (
    <div className="flex items-center justify-between py-1.5 group">
      <div className="flex items-center gap-1.5">
        <span className="text-xs text-foreground">{label}</span>
        {tooltip && <InfoTooltip text={tooltip} />}
      </div>
      <Toggle checked={checked} onChange={onChange} disabled={disabled} />
    </div>
  );
}

export { Toggle };
