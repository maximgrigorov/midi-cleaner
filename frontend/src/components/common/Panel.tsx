import { useState, type ReactNode } from 'react';
import * as Icons from './Icons';

interface PanelProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export default function Panel({
  title,
  children,
  defaultOpen = true,
}: PanelProps) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-border">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-2.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
      >
        {title}
        <span
          style={{
            transform: open ? 'rotate(180deg)' : 'rotate(0)',
            transition: 'transform 0.2s',
            display: 'inline-block',
          }}
        >
          <Icons.ChevronDown size={14} />
        </span>
      </button>
      <div
        style={{
          maxHeight: open ? '2000px' : '0',
          opacity: open ? 1 : 0,
          overflow: 'hidden',
          transition: 'all 0.2s',
        }}
      >
        <div className="px-4 pb-3 space-y-2">{children}</div>
      </div>
    </div>
  );
}
