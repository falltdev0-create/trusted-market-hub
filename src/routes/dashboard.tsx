import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Home, Search, MessageSquare, Bell, FileText, Eye, ArrowLeft,
  ShieldCheck, BadgeCheck, Clock, AlertTriangle, Loader2, RotateCcw, CheckCircle2,
  TrendingUp, TrendingDown,
} from "lucide-react";

import { toast } from "sonner";
import { useAuthStore } from "@/stores/auth";
import { usersApi, tryApi } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "لوحة التحكم — معاملاتي" }] }),
  component: Dashboard,
});

interface MeResponse {
  id?: string;
  full_name?: string;
  name?: string;
  email?: string;
  phone?: string;
  kyc_status?: "unverified" | "pending" | "verified" | "rejected";
  stats?: {
    listings?: number;
    conversations?: number;
    views?: number;
    notifications?: number;
  };
}

const KYC_META: Record<string, { label: string; cls: string; icon: any }> = {
  verified: { label: "موثّق", cls: "bg-success/10 text-success", icon: BadgeCheck },
  pending: { label: "قيد المراجعة", cls: "bg-warning/10 text-warning", icon: Clock },
  rejected: { label: "مرفوض", cls: "bg-destructive/10 text-destructive", icon: AlertTriangle },
  unverified: { label: "غير موثّق", cls: "bg-secondary text-muted-foreground", icon: ShieldCheck },
};

function Dashboard() {
  const { isLoggedIn, user } = useAuthStore();
  const nav = useNavigate();
  const qc = useQueryClient();
  const prevStatus = useRef<string | null>(null);

  useEffect(() => { if (!isLoggedIn) nav({ to: "/login" }); }, [isLoggedIn, nav]);

  const { data: me, isLoading } = useQuery<MeResponse>({
    queryKey: ["users", "me"],
    queryFn: () =>
      tryApi(
        () => usersApi.me().then((r) => r.data as MeResponse),
        {
          full_name: user?.name,
          email: user?.email,
          kyc_status: "unverified",
          stats: { listings: 3, conversations: 5, views: 124, notifications: 2 },
        },
      ),
    enabled: isLoggedIn,
    refetchInterval: (query) => {
      const status = (query.state.data as MeResponse | undefined)?.kyc_status;
      // Poll every 5s while pending so UI auto-updates when admin approves/rejects
      return status === "pending" ? 5000 : false;
    },
  });

  const kycStatus = (me?.kyc_status ?? "unverified") as keyof typeof KYC_META;

  // Notify user when status transitions from pending → verified / rejected
  useEffect(() => {
    const prev = prevStatus.current;
    const curr = kycStatus;
    if (prev === "pending" && curr === "verified") {
      toast.success("تهانينا! تم توثيق هويتك بنجاح", { icon: <CheckCircle2 className="h-4 w-4" /> });
    } else if (prev === "pending" && curr === "rejected") {
      toast.error("تم رفض طلب التحقق. يمكنك إعادة المحاولة بعد مراجعة المستندات.", { icon: <AlertTriangle className="h-4 w-4" /> });
    }
    prevStatus.current = curr;
  }, [kycStatus]);

  const startKyc = useMutation({
    mutationFn: () => tryApi(() => usersApi.startKyc().then((r) => r.data), { status: "pending" }),
    onSuccess: () => {
      toast.success("تم إرسال طلب التحقق من الهوية");
      qc.invalidateQueries({ queryKey: ["users", "me"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "فشل طلب التحقق"),
  });

  const kyc = KYC_META[kycStatus];
  const stats = me?.stats ?? {};
  const name = me?.full_name ?? me?.name ?? user?.name ?? "";

  const sparkFor = (n: number) =>
    Array.from({ length: 8 }, (_, i) => Math.max(1, Math.round((n || 1) * (0.4 + Math.sin(i + (n % 7)) * 0.3 + i * 0.08))));

  const trustScore =
    kycStatus === "verified" ? 95 : kycStatus === "pending" ? 60 : kycStatus === "rejected" ? 25 : 40;

  const cards = [
    { i: FileText, l: "إعلاناتي", v: stats.listings ?? 0, to: "/my-listings" as const, params: undefined, trend: 12 },
    { i: MessageSquare, l: "المحادثات", v: stats.conversations ?? 0, to: "/chat/$conversationId" as const, params: { conversationId: "1" }, trend: 8 },
    { i: Eye, l: "المشاهدات", v: stats.views ?? 0, to: undefined, params: undefined, trend: 24 },
    { i: Bell, l: "الإشعارات", v: stats.notifications ?? 0, to: "/notifications" as const, params: undefined, trend: -3 },
  ];


  return (
    <div className="mx-auto max-w-7xl px-4 py-10">
      <div className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">مرحباً {name} 👋</h1>
          <p className="text-muted-foreground">ماذا تريد أن تفعل اليوم؟</p>
        </div>
        <div className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-semibold transition-all ${kyc.cls} ${kycStatus === "verified" ? "animate-pulse shadow-[0_0_12px_rgba(34,197,94,0.35)]" : ""}`}>
          <kyc.icon className="h-4 w-4" /> الهوية: {kyc.label}
        </div>
      </div>

      {/* KYC banner */}
      {kycStatus !== "verified" && (
        <div className="mb-8 flex flex-col items-start justify-between gap-3 rounded-2xl border border-warning/30 bg-gradient-to-bl from-warning/10 to-transparent p-5 sm:flex-row sm:items-center">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-6 w-6 text-warning" />
            <div>
              <div className="font-bold">
                {kycStatus === "pending" ? "طلب التحقق قيد المراجعة" :
                 kycStatus === "rejected" ? "تم رفض التحقق — أعد المحاولة" :
                 "أكمل التحقق من الهوية لتفعيل النشر"}
              </div>
              <p className="text-sm text-muted-foreground">
                {kycStatus === "pending"
                  ? "نراجع مستنداتك الآن. ستصلك إشعار فوراً عند اكتمال المراجعة."
                  : "التحقق يمنح حسابك شارة موثّقة ويسمح بنشر إعلانات بدون قيود."}
              </p>
            </div>
          </div>
          <button
          disabled={kycStatus === "pending" || startKyc.isPending}
          onClick={() => nav({ to: "/verification" })}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-60"
          >
            {startKyc.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {kycStatus === "pending" ? (
              <>
                <Clock className="h-4 w-4" /> قيد المراجعة
              </>
            ) : kycStatus === "rejected" ? (
              <>
                <RotateCcw className="h-4 w-4" /> أعد المحاولة
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" /> إكمال التحقق
              </>
            )}
          </button>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        <Link
          to="/sell/new"
          className="group relative overflow-hidden rounded-2xl border bg-gradient-to-bl from-primary to-primary-light p-8 text-primary-foreground transition hover:-translate-y-1 hover:shadow-[var(--shadow-elevated)]"
        >
          <Home className="h-12 w-12 opacity-90" />
          <h2 className="mt-4 text-2xl font-extrabold">أنا بائع</h2>
          <p className="mt-2 text-white/90">أريد بيع أو تأجير عقار </p>
          <span className="mt-6 inline-flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 font-bold text-accent-foreground">
            ابدأ الآن <ArrowLeft className="h-4 w-4" />
          </span>
        </Link>

        <Link
          to="/marketplace"
          className="group relative overflow-hidden rounded-2xl border bg-card p-8 transition hover:-translate-y-1 hover:shadow-[var(--shadow-elevated)]"
        >
          <Search className="h-12 w-12 text-primary" />
          <h2 className="mt-4 text-2xl font-extrabold">أنا مشتري</h2>
          <p className="mt-2 text-muted-foreground">أريد شراء أو إيجار عقار  </p>
          <span className="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 font-bold text-primary-foreground">
            تصفح المعرض <ArrowLeft className="h-4 w-4" />
          </span>
        </Link>
      </div>

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((s) => {
          const up = s.trend >= 0;
          const inner = (
            <div className="rounded-xl border bg-card p-5 transition hover:shadow-[var(--shadow-card)]">
              <div className="flex items-center justify-between">
                <div className="rounded-lg bg-primary/10 p-3">
                  <s.i className="h-6 w-6 text-primary" />
                </div>
                <span
                  className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold ${
                    up ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"
                  }`}
                >
                  {up ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {Math.abs(s.trend)}%
                </span>
              </div>
              <div className="mt-4 text-2xl font-bold">
                {isLoading ? "…" : s.v.toLocaleString("ar-EG")}
              </div>
              <div className="text-sm text-muted-foreground">{s.l}</div>
              <Sparkline values={sparkFor(s.v)} positive={up} />
            </div>
          );
          return s.to ? (
            <Link key={s.l} to={s.to as any} params={s.params as any}>{inner}</Link>
          ) : (
            <div key={s.l}>{inner}</div>
          );
        })}
      </div>

      {/* Trust score ring */}
      <div className="mt-10 rounded-2xl border bg-card p-6">
        <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-bold">درجة الثقة في حسابك</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              تتحسن درجة ثقتك مع التحقق من الهوية، اكتمال الملف، وجودة إعلاناتك.
            </p>
          </div>
          <TrustRing value={trustScore} />
        </div>
      </div>
    </div>
  );
}

function Sparkline({ values, positive }: { values: number[]; positive: boolean }) {
  const w = 120;
  const h = 36;
  const max = Math.max(...values, 1);
  const step = w / (values.length - 1);
  const pts = values.map((v, i) => `${i * step},${h - (v / max) * (h - 4) - 2}`).join(" ");
  const color = positive ? "var(--color-success)" : "var(--color-destructive)";
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="mt-3 h-9 w-full" preserveAspectRatio="none" aria-hidden="true">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TrustRing({ value }: { value: number }) {
  const r = 45;
  const c = 2 * Math.PI * r;
  const offset = c - (Math.max(0, Math.min(100, value)) / 100) * c;
  return (
    <div className="relative h-32 w-32">
      <svg viewBox="0 0 100 100" className="h-32 w-32 -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="var(--color-secondary)" strokeWidth="8" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke="var(--color-primary)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          className="stroke-draw"
          style={{ ["--full" as any]: c, ["--target" as any]: offset }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-2xl font-extrabold text-primary">{value}</div>
        <div className="text-[10px] text-muted-foreground">من 100</div>
      </div>
    </div>
  );
}

