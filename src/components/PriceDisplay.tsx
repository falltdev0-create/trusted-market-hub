export function PriceDisplay({
  amount,
  currency = "جنيه",
  size = "md",
}: {
  amount: number;
  currency?: string;
  size?: "sm" | "md" | "lg";
}) {
  const cls =
    size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <span className={`font-bold text-primary ${cls}`}>
      {amount.toLocaleString("ar-EG")} <span className="text-xs font-semibold text-muted-foreground">{currency}</span>
    </span>
  );
}
