import * as Icons from './Icons';

interface EmptyStateProps {
  title: string;
  description: string;
}

export default function EmptyState({ title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center p-8">
      <div className="rounded-full bg-surface-2 p-5">
        <Icons.Music size={32} className="text-muted-foreground" />
      </div>
      <div>
        <h3 className="text-sm font-medium text-foreground mb-1">{title}</h3>
        <p className="text-xs text-muted-foreground max-w-[240px]">
          {description}
        </p>
      </div>
    </div>
  );
}
