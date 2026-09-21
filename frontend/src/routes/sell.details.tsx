import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { StepProgress } from "@/components/StepProgress";
import { useListingStore } from "@/stores/listing";
import { CITIES, CAR_BRANDS } from "@/lib/mock-data";

export const Route = createFileRoute("/sell/details")({
  head: () => ({ meta: [{ title: "بيانات الإعلان — مسكن" }] }),
  component: Details,
});

function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-semibold">{label}</label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20";

function Details() {
  const { draft, setDetails } = useListingStore();
  const isProperty = draft.kind?.includes("property");
  const [form, setForm] = useState<any>(draft.details ?? {});
  const nav = useNavigate();

  function up(k: string, v: any) {
    setForm((s: any) => ({ ...s, [k]: v }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setDetails(form);
    if (draft.id && !draft.id.startsWith("local-")) {
      try { await (await import("@/lib/api")).listingsApi.updateDetails(draft.id, form); } catch {}
    }
    nav({ to: "/sell/set-price" });
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <StepProgress current={5} total={6} label="بيانات الإعلان" />
      <h1 className="mb-6 text-3xl font-bold">أدخل بيانات الإعلان</h1>

      <form onSubmit={submit} className="space-y-5 rounded-2xl border bg-card p-6">
        <Field label="عنوان الإعلان">
          <input
            required
            className={inputCls}
            value={form.title ?? ""}
            onChange={(e) => up("title", e.target.value)}
          />
        </Field>
        <Field label="الوصف">
          <textarea
            required
            rows={4}
            className={inputCls}
            value={form.description ?? ""}
            onChange={(e) => up("description", e.target.value)}
          />
        </Field>

        {isProperty ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="المدينة">
                <select
                  required
                  className={inputCls}
                  value={form.city ?? ""}
                  onChange={(e) => up("city", e.target.value)}
                >
                  <option value="">اختر المدينة</option>
                  {CITIES.map((c) => (
                    <option key={c}>{c}</option>
                  ))}
                </select>
              </Field>
              <Field label="الحي">
                <input
                  required
                  className={inputCls}
                  value={form.area ?? ""}
                  onChange={(e) => up("area", e.target.value)}
                />
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              <Field label="المساحة (م²)">
                <input
                  type="number"
                  required
                  className={inputCls}
                  value={form.size ?? ""}
                  onChange={(e) => up("size", +e.target.value)}
                />
              </Field>
              <Field label="عدد الغرف">
                <input
                  type="number"
                  min={1}
                  max={10}
                  required
                  className={inputCls}
                  value={form.bedrooms ?? ""}
                  onChange={(e) => up("bedrooms", +e.target.value)}
                />
              </Field>
              <Field label="عدد الحمامات">
                <input
                  type="number"
                  min={1}
                  max={5}
                  required
                  className={inputCls}
                  value={form.bathrooms ?? ""}
                  onChange={(e) => up("bathrooms", +e.target.value)}
                />
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="الطابق">
                <input
                  type="number"
                  className={inputCls}
                  value={form.floor ?? ""}
                  onChange={(e) => up("floor", +e.target.value)}
                />
              </Field>
              <Field label="عمر البناء (سنوات)">
                <input
                  type="number"
                  className={inputCls}
                  value={form.age ?? ""}
                  onChange={(e) => up("age", +e.target.value)}
                />
              </Field>
            </div>
            <div className="flex gap-6">
              <label className="flex items-center gap-2 text-sm font-semibold">
                <input
                  type="checkbox"
                  checked={!!form.parking}
                  onChange={(e) => up("parking", e.target.checked)}
                />
                مواقف سيارات
              </label>
              <label className="flex items-center gap-2 text-sm font-semibold">
                <input
                  type="checkbox"
                  checked={!!form.garden}
                  onChange={(e) => up("garden", e.target.checked)}
                />
                حديقة
              </label>
            </div>
          </>
        ) : (
          <>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="الماركة">
                <select
                  required
                  className={inputCls}
                  value={form.brand ?? ""}
                  onChange={(e) => up("brand", e.target.value)}
                >
                  <option value="">اختر الماركة</option>
                  {CAR_BRANDS.map((b) => (
                    <option key={b}>{b}</option>
                  ))}
                </select>
              </Field>
              <Field label="سنة الصنع">
                <select
                  required
                  className={inputCls}
                  value={form.year ?? ""}
                  onChange={(e) => up("year", +e.target.value)}
                >
                  <option value="">اختر السنة</option>
                  {Array.from({ length: 36 }, (_, i) => 2025 - i).map((y) => (
                    <option key={y}>{y}</option>
                  ))}
                </select>
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="المسافة المقطوعة (كم)">
                <input
                  type="number"
                  required
                  className={inputCls}
                  value={form.km ?? ""}
                  onChange={(e) => up("km", +e.target.value)}
                />
              </Field>
              <Field label="حجم المحرك">
                <select
                  required
                  className={inputCls}
                  value={form.engine ?? ""}
                  onChange={(e) => up("engine", e.target.value)}
                >
                  <option value="">اختر السعة</option>
                  {["1000cc", "1500cc", "2000cc", "2500cc", "3000cc", "4000cc", "5000cc"].map((e) => (
                    <option key={e}>{e}</option>
                  ))}
                </select>
              </Field>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="ناقل الحركة">
                <select
                  required
                  className={inputCls}
                  value={form.transmission ?? ""}
                  onChange={(e) => up("transmission", e.target.value)}
                >
                  <option value="">اختر</option>
                  <option>أوتوماتيك</option>
                  <option>يدوي</option>
                </select>
              </Field>
              <Field label="اللون">
                <input
                  required
                  className={inputCls}
                  value={form.color ?? ""}
                  onChange={(e) => up("color", e.target.value)}
                />
              </Field>
            </div>
          </>
        )}

        <div className="flex justify-end pt-4">
          <button className="rounded-lg bg-primary px-8 py-3 font-bold text-primary-foreground hover:bg-primary-light">
            متابعة لتحديد السعر
          </button>
        </div>
      </form>
    </div>
  );
}
