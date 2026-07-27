import { Link } from "@tanstack/react-router";
import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

type Props = {
  icon?: LucideIcon;
  title: string;
  description?: string;
  ctaText?: string;
  ctaHref?: string;
};

export function EmptyState({ icon: Icon = Inbox, title, description, ctaText, ctaHref }: Props) {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed bg-card px-6 py-16 text-center">
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
        <Icon className="h-8 w-8 text-primary" />
      </div>
      <h3 className="text-lg font-bold text-foreground">{title}</h3>
      {description && <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {ctaText && ctaHref && (
        <Link
          to={ctaHref}
          className="mt-6 rounded-md bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary-light"
        >
          {ctaText}
        </Link>
      )}
    </div>
  );
}
