import { BadgeCheck } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const LABELS = {
  identity: { label: "هوية موثّقة", desc: "تم التحقق من الهوية الوطنية للبائع." },
  ownership: { label: "ملكية موثّقة", desc: "تم التحقق من مستندات ملكية السلعة." },
  full: { label: "موثّق بالكامل", desc: "الهوية والملكية تم توثيقهما من قبل معاملاتي." },
} as const;

export function VerifiedBadge({
  type = "full",
  size = "md",
  pulse = false,
}: {
  type?: "identity" | "ownership" | "full";
  size?: "sm" | "md";
  pulse?: boolean;
}) {
  const m = LABELS[type];
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
