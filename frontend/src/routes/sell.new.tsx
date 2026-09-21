import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Home, Key, Car, CarFront, Check, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { useListingStore, type ListingKind, kindToParts } from "@/stores/listing";
import { StepProgress } from "@/components/StepProgress";
import { listingsApi, tryApi } from "@/lib/api";
import { useLanguage } from "@/i18n/LanguageContext";

export const Route = createFileRoute("/sell/new")({
  head: () => ({ meta: [{ title: "نوع الإعلان — مسكن" }] }),
  component: SellNew,
});

const KINDS: { k: ListingKind; icon: any; title: string; desc: string }[] = [
  { k: "sale_property", icon: Home, title: "selling.saleProperty", desc: "selling.salePropertyDescription" },
  { k: "rent_property", icon: Key, title: "selling.rentProperty", desc: "selling.rentPropertyDescription" },
  
];

function SellNew() {
  const { t } = useLanguage();
  const { draft, setKind, setId } = useListingStore();
  const nav = useNavigate();
  const [loading, setLoading] = useState(false);

  async function next() {
    if (!draft.kind) return;
    setLoading(true);
    try {
      const parts = kindToParts(draft.kind);
      const res = await tryApi(
        () => listingsApi.create({ kind: draft.kind, ...parts }).then((r) => r.data),
        { id: `local-${Date.now()}` },
      );
      const id = res?.id ?? res?.listing?.id ?? `local-${Date.now()}`;
      setId(id);
      nav({ to: "/sell/upload-images" });
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? t("selling.createFailed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <StepProgress current={1} total={6} label={t("selling.chooseType")} />
      <h1 className="mb-2 text-3xl font-bold">{t("selling.question")}</h1>
      <p className="mb-8 text-muted-foreground">{t("selling.chooseCategory")}</p>

      <div className="grid gap-4 sm:grid-cols-2">
        {KINDS.map((k) => {
          const selected = draft.kind === k.k;
          return (
            <button
              key={k.k}
              onClick={() => setKind(k.k)}
              className={`relative rounded-2xl border-2 bg-card p-8 text-right transition hover:-translate-y-1 hover:shadow-[var(--shadow-card)] ${
                selected ? "border-primary shadow-[var(--shadow-card)]" : "border-border"
              }`}
            >
              {selected && (
                <div className="absolute left-4 top-4 rounded-full bg-primary p-1.5 text-primary-foreground">
                  <Check className="h-4 w-4" />
                </div>
              )}
              <div
                className={`inline-flex rounded-xl p-3 ${
                  selected ? "bg-primary text-primary-foreground" : "bg-primary/10 text-primary"
                }`}
              >
                <k.icon className="h-8 w-8" />
              </div>
              <h3 className="mt-4 text-xl font-bold">{t(k.title)}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t(k.desc)}</p>
            </button>
          );
        })}
      </div>

      <div className="mt-8 flex justify-end">
        <button
          disabled={!draft.kind || loading}
          onClick={next}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-3 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />} {t("selling.continue")}
        </button>
      </div>
    </div>
  );
}
