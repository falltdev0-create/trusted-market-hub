import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Rocket, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { StepProgress } from "@/components/StepProgress";
import { useListingStore } from "@/stores/listing";
import { listingsApi } from "@/lib/api";

export const Route = createFileRoute("/sell/set-price")({
  head: () => ({ meta: [{ title: "تحديد السعر — معاملاتي" }] }),
  component: SetPrice,
});

function SetPrice() {
  const { draft, setPrice, reset } = useListingStore();
  const max = draft.priceMax ?? 1000000;
  const [price, setLocal] = useState(draft.price ?? Math.floor(max / 2));
  const [submitted, setSubmitted] = useState(false);
  const nav = useNavigate();

  async function submit() {
    if (price > max) { toast.error("السعر يتجاوز الحد المسموح"); return; }
    setPrice(price);
    if (draft.id && !draft.id.startsWith("local-")) {
      try {
        await listingsApi.setPrice(draft.id, price);
        await listingsApi.submitForReview(draft.id);
      } catch (e: any) {
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

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <StepProgress current={6} total={6} label="تحديد السعر" />
      <h1 className="mb-2 text-3xl font-bold">حدد سعر إعلانك</h1>
      <p className="mb-6 text-muted-foreground">
        الحد الأقصى المسموح:{" "}
        <span className="font-bold text-accent">{max.toLocaleString()} جنيه</span>
      </p>

      <div className="rounded-2xl border bg-card p-6">
        <label className="mb-2 block text-sm font-semibold">السعر المطلوب</label>
        <div className="relative">
          <input
            type="number"
            value={price}
            onChange={(e) => setLocal(+e.target.value)}
            className="w-full rounded-lg border-2 border-primary/20 bg-background px-4 py-4 pe-20 text-3xl font-bold text-primary outline-none focus:border-primary"
          />
          <span className="absolute end-4 top-1/2 -translate-y-1/2 text-sm font-semibold text-muted-foreground">
            جنيه
          </span>
        </div>

        <input
          type="range"
          min={0}
          max={max}
          step={1000}
          value={price}
          onChange={(e) => setLocal(+e.target.value)}
          className="mt-4 w-full accent-primary"
        />

        {price > max && (
          <div className="mt-3 flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" /> السعر يتجاوز الحد الأقصى المسموح
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
              <dd className="font-semibold">{draft.conditionScore}/100</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">السعر</dt>
              <dd className="font-bold text-primary">{price.toLocaleString()} جنيه</dd>
            </div>
          </dl>
        </div>

        <button
          onClick={submit}
          disabled={price > max || price <= 0}
          className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3.5 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
        >
          <Rocket className="h-5 w-5" /> رفع الإعلان للمراجعة
        </button>
      </div>
    </div>
  );
}
