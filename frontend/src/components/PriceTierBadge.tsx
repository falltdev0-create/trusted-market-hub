import { TrendingDown, Minus, TrendingUp } from "lucide-react";
import { useLanguage } from "@/i18n/LanguageContext";

export type PriceTier = "cheap" | "medium" | "expensive";


export function PriceTierBadge({
  tier,
  size = "md",
}: {
  tier: PriceTier;
  size?: "sm" | "md";
}) {
  const { t } = useLanguage();
  const m = { cheap: { label: t("pricing.cheap"), cls: "bg-success/10 text-success border-success/30", Icon: TrendingDown }, medium: { label: t("pricing.medium"), cls: "bg-primary/10 text-primary border-primary/30", Icon: Minus }, expensive: { label: t("pricing.expensive"), cls: "bg-destructive/10 text-destructive border-destructive/30", Icon: TrendingUp } }[tier];
  const px = size === "sm" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs";
  const ic = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border font-bold ${px} ${m.cls}`}
      title={m.label}
    >
      <m.Icon className={ic} /> {m.label}
    </span>
  );
}

/** Compute a tier from a price and category thresholds (kept in one place). */
const TIER_THRESHOLDS: Record<string, { cheap: number; medium: number }> = {
  property: { cheap: 500_000,  medium: 2_000_000 },
  house:    { cheap: 500_000,  medium: 2_000_000 },
  car:      { cheap: 800_000,  medium: 2_000_000 },
  other:    { cheap:  50_000,  medium:   250_000 },
};

export function computeTier(price: number, category: string = "other"): PriceTier {
  const t = TIER_THRESHOLDS[category] ?? TIER_THRESHOLDS.other;
  if (price <= t.cheap) return "cheap";
  if (price <= t.medium) return "medium";
  return "expensive";
}
