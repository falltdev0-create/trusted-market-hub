import { BadgeCheck } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useLanguage } from "@/i18n/LanguageContext";

export function VerifiedBadge({
  type = "full",
  size = "md",
  pulse = false,
}: {
  type?: "identity" | "ownership" | "full";
  size?: "sm" | "md";
  pulse?: boolean;
}) {
  const { t } = useLanguage();
  const m = { identity: { label: t("trust.identity"), desc: t("trust.identityDescription") }, ownership: { label: t("trust.ownership"), desc: t("trust.ownershipDescription") }, full: { label: t("trust.full"), desc: t("trust.fullDescription") } }[type];
  const sz = size === "sm" ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1";
  const icon = size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5";
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={`inline-flex items-center gap-1 rounded-full bg-success/15 font-semibold text-success ${sz} ${
              pulse ? "trust-pulse" : ""
            }`}
          >
            <BadgeCheck className={icon} />
            {m.label}
          </span>
        </TooltipTrigger>
        <TooltipContent>{m.desc}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
