import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus, Eye, Pencil, Trash2 } from "lucide-react";
import { MOCK_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/my-listings")({
  head: () => ({ meta: [{ title: "إعلاناتي — معاملاتي" }] }),
  component: MyListings,
});

const STAGES = [
  "مسودة",
  "صور مرفوعة",
  "تحقق الحالة",
  "وثائق مرفوعة",
  "وثائق موثّقة",
  "سعر محدد",
  "قيد المراجعة",
  "منشور",
];

const items = MOCK_LISTINGS.slice(0, 3).map((l, i) => ({
  ...l,
  status: [7, 6, 3][i],
  publishedAt: "2025-05-12",
}));

const statusColor = (i: number) =>
  i === 7
    ? "bg-success/10 text-success"
    : i === 6
      ? "bg-warning/10 text-warning"
      : "bg-primary/10 text-primary";

function MyListings() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">إعلاناتي</h1>
          <p className="text-muted-foreground">{items.length} إعلانات</p>
        </div>
        <Link
          to="/sell/new"
          className="flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-bold text-primary-foreground hover:bg-primary-light"
        >
          <Plus className="h-4 w-4" /> إعلان جديد
        </Link>
      </div>

      <div className="space-y-4">
        {items.map((l) => (
          <div
            key={l.id}
            className="rounded-2xl border bg-card p-4 transition hover:shadow-[var(--shadow-card)]"
          >
            <div className="flex flex-col gap-4 sm:flex-row">
              <img
                src={l.image}
                alt=""
                className="h-32 w-full flex-shrink-0 rounded-lg object-cover sm:w-48"
              />
              <div className="flex-1">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <h3 className="font-bold">{l.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {l.city} — نُشر {l.publishedAt}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span
                      className={`rounded-md px-2.5 py-1 text-xs font-bold ${statusColor(l.status)}`}
                    >
                      {STAGES[l.status]}
                    </span>
                    <span className="rounded-md bg-warning/10 px-2.5 py-1 text-xs font-bold text-warning">
                      ⭐ {l.grade === "excellent" ? "ممتازة" : "جيدة"}
                    </span>
                  </div>
                </div>

                <div className="mt-3 text-lg font-bold text-primary">
                  {l.price.toLocaleString()} جنيه
                </div>

                {/* Pipeline */}
                <div className="mt-4 hidden md:block">
                  <div className="flex items-center gap-1">
                    {STAGES.map((s, i) => (
                      <div key={s} className="flex flex-1 items-center">
                        <div
                          className={`h-1.5 w-full rounded ${
                            i <= l.status ? "bg-primary" : "bg-secondary"
                          }`}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="mt-1 flex justify-between text-[10px] text-muted-foreground">
                    {STAGES.map((s) => (
                      <span key={s} className="flex-1 text-center">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <Link
                    to="/listing/$id"
                    params={{ id: l.id }}
                    className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-semibold hover:bg-secondary"
                  >
                    <Eye className="h-3.5 w-3.5" /> عرض
                  </Link>
                  <button className="flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-semibold hover:bg-secondary">
                    <Pencil className="h-3.5 w-3.5" /> تعديل
                  </button>
                  <button className="flex items-center gap-1 rounded-md border border-destructive/30 px-3 py-1.5 text-xs font-semibold text-destructive hover:bg-destructive/10">
                    <Trash2 className="h-3.5 w-3.5" /> حذف
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
