interface Props {
  current: number;
  total: number;
  label: string;
}

export function StepProgress({ current, total, label }: Props) {
  const pct = (current / total) * 100;
  return (
    <div className="mb-8">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="font-semibold text-primary">
          الخطوة {current} من {total}
        </span>
        <span className="text-muted-foreground">{label}</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full bg-primary transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
