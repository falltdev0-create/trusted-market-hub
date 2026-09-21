import { useLanguage } from "@/i18n/LanguageContext";

export function PriceDisplay({
  amount,
  currency,
  size = "md",
}: {
  amount: number;
  currency?: string;
  size?: "sm" | "md" | "lg";
}) {
  const { t } = useLanguage();
  const cls =
    size === "lg" ? "text-2xl" : size === "sm" ? "text-sm" : "text-lg";
  return (
    <span className={`font-bold text-primary ${cls}`}>
      {amount.toLocaleString("ar-EG")} <span className="text-xs font-semibold text-muted-foreground">{currency ?? t("common.currency")}</span>
    </span>
  );
}
