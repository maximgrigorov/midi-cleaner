import * as Icons from './Icons';

export default function InfoTooltip({ text }: { text: string }) {
  return (
    <span className="tip-wrap">
      <button
        type="button"
        className="inline-flex items-center justify-center rounded-sm p-0.5 text-muted-foreground hover:text-foreground transition-colors"
      >
        <Icons.Help size={14} />
      </button>
      <span className="tip-text">{text}</span>
    </span>
  );
}
