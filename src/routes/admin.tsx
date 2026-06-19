import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  ClipboardList,
  CheckCircle2,
  XCircle,
  Users,
  Bot,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth";
import { MOCK_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/admin")({
  head: () => ({ meta: [{ title: "لوحة الإدارة — معاملاتي" }] }),
  component: Admin,
});

const NAV = [
  { id: "dash", label: "لوحة التحكم", icon: LayoutDashboard },
  { id: "pending", label: "قيد المراجعة", icon: ClipboardList },
  { id: "approved", label: "الإعلانات المنشورة", icon: CheckCircle2 },
  { id: "rejected", label: "المرفوضة", icon: XCircle },
  { id: "users", label: "المستخدمون", icon: Users },
] as const;

function Admin() {
  const { user, isLoggedIn } = useAuthStore();
  const nav = useNavigate();
  const [tab, setTab] = useState<(typeof NAV)[number]["id"]>("dash");
  const [reviewing, setReviewing] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoggedIn || user?.role !== "admin") nav({ to: "/login" });
  }, [isLoggedIn, user, nav]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <aside className="rounded-2xl border bg-card p-3">
          <ul className="space-y-1">
            {NAV.map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => {
                    setTab(n.id);
                    setReviewing(null);
                  }}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
                    tab === n.id
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-secondary"
                  }`}
                >
                  <n.icon className="h-4 w-4" /> {n.label}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main>
          {reviewing ? (
            <ReviewListing id={reviewing} onClose={() => setReviewing(null)} />
          ) : tab === "dash" ? (
            <Dash />
          ) : tab === "pending" ? (
            <PendingList onOpen={setReviewing} />
          ) : (
            <div className="rounded-2xl border bg-card p-12 text-center text-muted-foreground">
              قسم {NAV.find((n) => n.id === tab)?.label} — تجريبي
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function Dash() {
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">لوحة التحكم</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { l: "المنتظرة", v: 12, c: "bg-warning/10 text-warning" },
          { l: "المنشورة", v: 247, c: "bg-success/10 text-success" },
          { l: "المرفوضة", v: 8, c: "bg-destructive/10 text-destructive" },
          { l: "المستخدمون", v: 1432, c: "bg-primary/10 text-primary" },
        ].map((s) => (
          <div key={s.l} className="rounded-2xl border bg-card p-5">
            <div className={`inline-flex rounded-lg px-2.5 py-1 text-xs font-bold ${s.c}`}>
              {s.l}
            </div>
            <div className="mt-3 text-3xl font-extrabold">{s.v.toLocaleString()}</div>
          </div>
        ))}
      </div>

      <h2 className="mt-10 mb-4 text-xl font-bold">نشاط حديث</h2>
      <div className="space-y-2 rounded-2xl border bg-card p-4">
        {[
          "إعلان جديد قيد المراجعة: شقة فاخرة في الخرطوم 2",
         
          "مستخدم جديد سجل في المنصة",
        ].map((t, i) => (
          <div key={i} className="border-b py-2 text-sm last:border-0">
            {t}
          </div>
        ))}
      </div>
    </div>
  );
}

function PendingList({ onOpen }: { onOpen: (id: string) => void }) {
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">قيد المراجعة</h1>
      <div className="space-y-3">
        {MOCK_LISTINGS.slice(0, 4).map((l) => (
          <div
            key={l.id}
            className="flex items-center gap-4 rounded-xl border bg-card p-4"
          >
            <img src={l.image} alt="" className="h-16 w-24 rounded object-cover" />
            <div className="flex-1">
              <div className="font-bold">{l.title}</div>
              <div className="text-sm text-muted-foreground">
                {l.city} — {l.price.toLocaleString()} جنيه
              </div>
            </div>
            <button
              onClick={() => onOpen(l.id)}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground hover:bg-primary-light"
            >
              مراجعة
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ReviewListing({ id, onClose }: { id: string; onClose: () => void }) {
  const l = MOCK_LISTINGS.find((x) => x.id === id)!;
  const [rejecting, setRejecting] = useState(false);
  const [reason, setReason] = useState("");

  function approve() {
    toast.success("تم قبول الإعلان ونشره");
    onClose();
  }
  function reject() {
    if (!reason.trim()) {
      toast.error("اكتب سبب الرفض");
      return;
    }
    toast.error("تم رفض الإعلان");
    onClose();
  }

  return (
    <div>
      <button onClick={onClose} className="mb-4 text-sm text-muted-foreground hover:text-primary">
        ← العودة للقائمة
      </button>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <img src={l.image} alt="" className="aspect-video w-full rounded-2xl object-cover" />
          <h2 className="mt-4 text-xl font-bold">{l.title}</h2>
          <p className="text-sm text-muted-foreground">{l.city}</p>
          <p className="mt-2 text-2xl font-bold text-primary">{l.price.toLocaleString()} جنيه</p>
        </div>

        <div className="rounded-2xl border bg-card p-5">
          <div className="flex items-center gap-2 font-bold">
            <Bot className="h-5 w-5 text-primary" /> تقييم الحالة
          </div>
          <div className="my-4 text-center">
            <div className="text-4xl font-extrabold text-success">87/100</div>
            <div className="mt-1 text-sm text-success">درجة أولى</div>
          </div>
          <ul className="space-y-1.5 text-sm">
            <li className="flex justify-between"><span>الحالة العامة</span><b>92</b></li>
            <li className="flex justify-between"><span>جودة الصور</span><b>85</b></li>
            <li className="flex justify-between"><span>النظافة</span><b>88</b></li>
          </ul>
        </div>

        <div className="rounded-2xl border bg-card p-5">
          <div className="flex items-center gap-2 font-bold">
            <ShieldCheck className="h-5 w-5 text-success" /> التحقق من الوثائق
          </div>
          <div className="my-4 text-center">
            <div className="text-4xl font-extrabold text-success">94%</div>
            <div className="mt-1 text-sm text-muted-foreground">نسبة المطابقة</div>
          </div>
          <div className="space-y-1.5 text-sm">
            <div className="text-success">✓ الاسم مطابق</div>
            <div className="text-success">✓ الرقم الوطني مطابق</div>
            <div className="text-success">✓ صورة الهوية واضحة</div>
            <div className="text-success">✓ وثيقة الملكية أصلية</div>
          </div>
        </div>
      </div>

      {rejecting ? (
        <div className="mt-6 rounded-2xl border bg-card p-5">
          <h3 className="font-bold">سبب الرفض</h3>
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            className="mt-2 w-full rounded-lg border bg-card p-3 outline-none focus:border-primary"
          />
          <div className="mt-3 flex justify-end gap-2">
            <button onClick={() => setRejecting(false)} className="rounded-md px-4 py-2 text-sm font-semibold hover:bg-secondary">
              إلغاء
            </button>
            <button onClick={reject} className="rounded-md bg-destructive px-4 py-2 text-sm font-bold text-destructive-foreground">
              تأكيد الرفض
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-6 flex gap-3">
          <button
            onClick={approve}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-success py-3 font-bold text-success-foreground hover:opacity-90"
          >
            <CheckCircle2 className="h-5 w-5" /> قبول ونشر
          </button>
          <button
            onClick={() => setRejecting(true)}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-destructive py-3 font-bold text-destructive-foreground hover:opacity-90"
          >
            <XCircle className="h-5 w-5" /> رفض مع السبب
          </button>
        </div>
      )}
    </div>
  );
}
