import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Rocket, Info } from "lucide-react";
import { toast } from "sonner";
import { StepProgress } from "@/components/StepProgress";
import { useListingStore } from "@/stores/listing";
import { listingsApi, tryApi } from "@/lib/api";
import { PriceTierBadge, computeTier, type PriceTier } from "@/components/PriceTierBadge";

export const Route = createFileRoute("/sell/set-price")({
  head: () => ({
    meta: [
      { title: "تحديد السعر — معاملاتي" },
      { name: "description", content: "حدد سعر إعلانك بحرية. سيظهر تصنيف السعر (رخيص/متوسط/غالي) تلقائياً للمشترين." },
    ],
  }),
  component: SetPrice,
});

type Estimate = {
  suggested_min: number;
  suggested_max: number;
  market_avg?: number;
  tier?: PriceTier;
};

function SetPrice() {
  const { draft, setPrice, reset } = useListingStore();
  const category = draft.kind?.split("_")[1] ?? "property";
  const [price, setLocal] = useState<number>(draft.price ?? 100_000);
  const [estimate, setEst] = useState<Estimate | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const nav = useNavigate();

  // Fetch AI price estimate (informational — not a cap)
  useEffect(() => {
    if (!draft.id || draft.id.startsWith("local-")) {
      // offline hint
      const fallback: Record<string, Estimate> = {
        property: { suggested_min: 500_000, suggested_max: 3_000_000, market_avg: 1_500_000 },
        house:    { suggested_min: 500_000, suggested_max: 3_000_000, market_avg: 1_500_000 },
        car:      { suggested_min: 800_000, suggested_max: 3_500_000, market_avg: 1_800_000 },
      };
      setEst(fallback[category] ?? fallback.property);
      return;
    }
    (async () => {
      const data = await tryApi(
        () => listingsApi.priceEstimate(draft.id!).then((r) => r.data as Estimate),
        { suggested_min: 500_000, suggested_max: 3_000_000, market_avg: 1_500_000 },
      );
      setEst(data);
    })();
  }, [draft.id, category]);

  const tier: PriceTier = estimate?.tier
    ? computeTier(price, category)  // recompute against user-entered price
    : computeTier(price, category);

  async function submit() {
    if (!price || price <= 0) {
      toast.error("أدخل سعراً صحيحاً");
      return;
    }
    setPrice(price);
    setSubmitting(true);
    if (draft.id && !draft.id.startsWith("local-")) {
      try {
        await listingsApi.setPrice(draft.id, price);
        await listingsApi.submitForReview(draft.id);
      } catch (e: any) {
        setSubmitting(false);
        toast.error(e?.response?.data?.detail ?? "تعذّر رفع الإعلان");
        return;
      }
    }
    toast.success("تم رفع الإعلان للمراجعة");
    setSubmitted(true);
    setTimeout(() => { reset(); nav({ to: "/my-listings" }); }, 2200);
  }

  if (submitted) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="text-7xl">🎉</div>
        <h1 className="mt-4 text-3xl font-extrabold text-success">تم إرسال إعلانك للمراجعة</h1>
        <p className="mt-2 text-muted-foreground">سيتم نشره خلال 24 ساعة بعد المراجعة البشرية.</p>
      </div>
    );
  }

  const mid = estimate ? Math.round((estimate.suggested_min + estimate.suggested_max) / 2) : 0;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <StepProgress current={6} total={6} label="تحديد السعر" />
      <h1 className="mb-2 text-3xl font-bold">حدد سعر إعلانك بحرية</h1>
      <p className="mb-6 text-muted-foreground">
        أنت تختار السعر — والذكاء الاصطناعي يعرض تصنيفاً إرشادياً للمشترين (رخيص / متوسط / غالي).
      </p>

      {/* Estimate card */}
      {estimate && (
        <div className="mb-6 rounded-2xl border bg-primary/5 p-5">
          <div className="mb-3 flex items-center gap-2 font-bold text-primary">
            <Info className="h-5 w-5" /> الإرشاد التسعيري
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-xs text-muted-foreground">نطاق منخفض</div>
              <div className="text-lg font-extrabold">{estimate.suggested_min.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">متوسط السوق</div>
              <div className="text-lg font-extrabold text-primary">{(estimate.market_avg ?? mid).toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">نطاق مرتفع</div>
              <div className="text-lg font-extrabold">{estimate.suggested_max.toLocaleString()}</div>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-2xl border bg-card p-6">
        <div className="mb-2 flex items-center justify-between">
          <label className="block text-sm font-semibold">السعر المطلوب (بحرية)</label>
          <PriceTierBadge tier={tier} />
        </div>
        <div className="relative">
          <input
            type="number"
            min={0}
            value={price}
            onChange={(e) => setLocal(+e.target.value)}
            className="w-full rounded-lg border-2 border-primary/20 bg-background px-4 py-4 pe-20 text-3xl font-bold text-primary outline-none focus:border-primary"
          />
          <span className="absolute end-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-muted-foreground">
            جنيه
          </span>
        </div>

        <p className="mt-3 text-xs text-muted-foreground">
          لا يوجد حد أقصى ثابت. سيتم عرض التصنيف السعري بجانب إعلانك حتى يستطيع المشترون المقارنة.
        </p>

        {estimate && (price < estimate.suggested_min * 0.5 || price > estimate.suggested_max * 2) && (
          <div className="mt-3 rounded-lg bg-warning/10 p-3 text-sm text-warning">
            سعرك بعيد جداً عن نطاق السوق. هذا مسموح لكنه قد يقلّل من إقبال المشترين.
          </div>
        )}

        <div className="mt-8 rounded-xl bg-secondary p-5">
          <h3 className="font-bold">ملخص الإعلان</h3>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">العنوان</dt>
              <dd className="font-semibold">{draft.details?.title ?? "—"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">الحالة</dt>
              <dd className="font-semibold">{draft.conditionScore ?? "—"}/100</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">السعر</dt>
              <dd className="font-bold text-primary">{price.toLocaleString()} جنيه</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">التصنيف</dt>
              <dd><PriceTierBadge tier={tier} size="sm" /></dd>
            </div>
          </dl>
        </div>

        <button
          onClick={submit}
          disabled={submitting || price <= 0}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3.5 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
        >
          <Rocket className="h-5 w-5" /> {submitting ? "جاري الرفع..." : "رفع الإعلان للمراجعة"}
        </button>
      </div>
    </div>
  );
}
