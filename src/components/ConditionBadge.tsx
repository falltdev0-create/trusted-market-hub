type Grade = "excellent" | "good" | "poor";

const MAP: Record<Grade, { label: string; cls: string; stars: number }> = {
  excellent: { label: "درجة اولى", cls: "bg-success/15 text-success border-success/30", stars: 3 },
  good: { label: "درجة ثانية", cls: "bg-warning/15 text-warning-foreground border-warning/30", stars: 2 },
  poor: { label: "درجة ثالثة", cls: "bg-destructive/15 text-destructive border-destructive/30", stars: 1 },
};

export function ConditionBadge({
  grade,
  score,
  showScore,
}: {
  grade: Grade;
  score?: number;
  showScore?: boolean;
}) {
  const m = MAP[grade];
  return (
    <span
      className={`inline-flex animate-fade-in items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${m.cls}`}
    >
      <span aria-hidden="true">
        {Array.from({ length: 3 }).map((_, i) => (
          <span key={i} className={i < m.stars ? "opacity-100" : "opacity-25"}>
            ⭐
          </span>
        ))}
      </span>
      <span>{m.label}</span>
      {showScore && score != null && <span className="opacity-80">({score})</span>}
    </span>
  );
}
