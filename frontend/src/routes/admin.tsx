import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard, ClipboardList, Users, ShieldCheck, UserCog,
  FileWarning, Settings2, History, Loader2, Check, X, Search,
  Tags, BarChart3, Megaphone, Plus, Trash2,
} from "lucide-react";
import { toast } from "sonner";
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { useAuthStore } from "@/stores/auth";
import { adminApi, tryApi } from "@/lib/api";
import { MOCK_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/admin")({
  head: () => ({
    meta: [
      { title: "لوحة المشرفين — معاملاتي" },
      { name: "description", content: "لوحة إدارة هرمية لموقع معاملاتي: مراجعة الإعلانات، المستخدمين، التحقق، المشرفين، السجل، البلاغات، والإعدادات." },
    ],
  }),
  component: AdminPage,
});

type Tab =
  | "dash" | "listings" | "users" | "kyc"
  | "admins" | "logs" | "reports" | "categories" | "analytics" | "broadcast" | "settings";

const TABS: { id: Tab; label: string; icon: any; role: "any" | "super_admin" }[] = [
  { id: "dash",       label: "نظرة عامة",       icon: LayoutDashboard, role: "any" },
  { id: "listings",   label: "الإعلانات",       icon: ClipboardList,   role: "any" },
  { id: "users",      label: "المستخدمون",      icon: Users,           role: "any" },
  { id: "kyc",        label: "طلبات التحقق",    icon: ShieldCheck,     role: "any" },
  { id: "admins",     label: "المشرفون",        icon: UserCog,         role: "super_admin" },
  { id: "logs",       label: "سجل الإجراءات",   icon: History,         role: "any" },
  { id: "reports",    label: "البلاغات",        icon: FileWarning,     role: "any" },
  { id: "categories", label: "الفئات والأسعار", icon: Tags,            role: "super_admin" },
  { id: "analytics",  label: "التحليلات",       icon: BarChart3,       role: "any" },
  { id: "broadcast",  label: "إشعار جماعي",     icon: Megaphone,       role: "any" },
  { id: "settings",   label: "الإعدادات",       icon: Settings2,       role: "super_admin" },
];

function AdminPage() {
  const { user, isLoggedIn } = useAuthStore();
  const nav = useNavigate();
  const [tab, setTab] = useState<Tab>("dash");

  // Treat any admin/super_admin as authorized in the UI; the backend enforces the real hierarchy.
  const adminRole = (user as any)?.admin_role ?? (user?.role === "admin" ? "admin" : null);
  const isSuper = adminRole === "super_admin";

  useEffect(() => {
    if (!isLoggedIn) nav({ to: "/login" });
  }, [isLoggedIn, nav]);

  const visibleTabs = useMemo(
    () => TABS.filter((t) => t.role === "any" || isSuper),
    [isSuper],
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <aside className="rounded-2xl border bg-card p-3 lg:sticky lg:top-20 lg:h-fit">
          <div className="mb-3 rounded-lg bg-primary/5 p-3">
            <div className="text-xs text-muted-foreground">الدور</div>
            <div className="font-bold text-primary">
              {isSuper ? "مدير عام (Super Admin)" : adminRole ? adminRole : "مشرف"}
            </div>
          </div>
          <ul className="space-y-1">
            {visibleTabs.map((n) => (
              <li key={n.id}>
                <button
                  onClick={() => setTab(n.id)}
                  className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-semibold transition ${
                    tab === n.id ? "bg-primary text-primary-foreground" : "hover:bg-secondary"
                  }`}
                >
                  <n.icon className="h-4 w-4" /> {n.label}
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main>
          {tab === "dash"       && <DashTab />}
          {tab === "listings"   && <ListingsTab />}
          {tab === "users"      && <UsersTab />}
          {tab === "kyc"        && <KycTab />}
          {tab === "admins"     && <AdminsTab />}
          {tab === "logs"       && <LogsTab />}
          {tab === "reports"    && <ReportsTab />}
          {tab === "categories" && <CategoriesTab />}
          {tab === "analytics"  && <AnalyticsTab />}
          {tab === "broadcast"  && <BroadcastTab />}
          {tab === "settings"   && <SettingsTab />}
        </main>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── Dashboard ────────────────────
function DashTab() {
  const [stats, setStats] = useState<any>(null);
  useEffect(() => {
    tryApi(() => adminApi.getStats().then((r) => r.data), {
      total_users: 1432, pending_review: 12, published: 247, rejected: 8, total_admins: 4,
    }).then(setStats);
  }, []);
  const items = [
    { l: "قيد المراجعة",  v: stats?.pending_review, c: "bg-warning/10 text-warning" },
    { l: "المنشورة",       v: stats?.published,      c: "bg-success/10 text-success" },
    { l: "المرفوضة",       v: stats?.rejected,       c: "bg-destructive/10 text-destructive" },
    { l: "المستخدمون",     v: stats?.total_users,    c: "bg-primary/10 text-primary" },
  ];
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">نظرة عامة</h1>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((s) => (
          <div key={s.l} className="rounded-2xl border bg-card p-5">
            <div className={`inline-flex rounded-lg px-2.5 py-1 text-xs font-bold ${s.c}`}>{s.l}</div>
            <div className="mt-3 text-3xl font-extrabold">
              {stats == null ? <Loader2 className="h-6 w-6 animate-spin" /> : (s.v ?? 0).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── Listings ─────────────────────
function ListingsTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [reason, setReason] = useState<Record<string, string>>({});

  async function load() {
    const data = await tryApi(
      () => adminApi.getPendingListings(1).then((r) => r.data),
      MOCK_LISTINGS.slice(0, 5).map((l) => ({ id: l.id, title: l.title, category: l.category, price: l.price, city: l.city, created_at: new Date().toISOString() })),
    );
    setRows(data);
  }
  useEffect(() => { load(); }, []);

  async function approve(id: string) {
    setBusy(id);
    try {
      await adminApi.approveListing(id);
      toast.success("تم قبول الإعلان");
      setRows((r) => r?.filter((x) => x.id !== id) ?? null);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "فشل القبول");
    } finally { setBusy(null); }
  }
  async function reject(id: string) {
    const rs = reason[id]?.trim();
    if (!rs) { toast.error("اكتب سبب الرفض"); return; }
    setBusy(id);
    try {
      await adminApi.rejectListing(id, undefined, rs);
      toast.success("تم رفض الإعلان");
      setRows((r) => r?.filter((x) => x.id !== id) ?? null);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "فشل الرفض");
    } finally { setBusy(null); }
  }

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">إعلانات قيد المراجعة</h1>
      {rows == null ? <LoadingBlock /> :
        rows.length === 0 ? <EmptyBlock label="لا توجد إعلانات بانتظار المراجعة" /> : (
          <div className="space-y-3">
            {rows.map((l) => (
              <div key={l.id} className="rounded-xl border bg-card p-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1">
                    <div className="font-bold">{l.title}</div>
                    <div className="text-sm text-muted-foreground">
                      {l.city} • {l.category} • {Number(l.price ?? 0).toLocaleString()} جنيه
                    </div>
                  </div>
                  <button
                    disabled={busy === l.id}
                    onClick={() => approve(l.id)}
                    className="flex items-center gap-1 rounded-lg bg-success px-3 py-2 text-sm font-bold text-white hover:opacity-90 disabled:opacity-50"
                  >
                    <Check className="h-4 w-4" /> قبول
                  </button>
                </div>
                <div className="mt-3 flex gap-2">
                  <input
                    value={reason[l.id] ?? ""}
                    onChange={(e) => setReason((p) => ({ ...p, [l.id]: e.target.value }))}
                    placeholder="سبب الرفض..."
                    className="flex-1 rounded-lg border bg-background px-3 py-2 text-sm"
                  />
                  <button
                    disabled={busy === l.id}
                    onClick={() => reject(l.id)}
                    className="flex items-center gap-1 rounded-lg bg-destructive px-3 py-2 text-sm font-bold text-white hover:opacity-90 disabled:opacity-50"
                  >
                    <X className="h-4 w-4" /> رفض
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

// ─────────────────────────────────────────── Users ────────────────────────
function UsersTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [q, setQ] = useState("");
  useEffect(() => {
    tryApi(() => adminApi.listUsers({ q }).then((r) => r.data), [
      { id: "u1", full_name: "محمد أحمد", email: "m@example.com", kyc_status: "verified", is_active: true },
      { id: "u2", full_name: "فاطمة علي", email: "f@example.com", kyc_status: "pending", is_active: true },
    ]).then(setRows);
  }, [q]);

  return (
    <div>
      <h1 className="mb-4 text-3xl font-bold">المستخدمون</h1>
      <div className="relative mb-4">
        <Search className="absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="ابحث بالاسم أو البريد..." className="w-full rounded-lg border bg-card px-4 py-2.5 pe-10" />
      </div>
      {rows == null ? <LoadingBlock /> :
        rows.length === 0 ? <EmptyBlock label="لا يوجد مستخدمون" /> : (
          <div className="overflow-hidden rounded-xl border bg-card">
            <table className="w-full text-sm">
              <thead className="bg-secondary text-right">
                <tr><th className="p-3">الاسم</th><th className="p-3">البريد</th><th className="p-3">التحقق</th><th className="p-3">الحالة</th><th className="p-3">إجراء</th></tr>
              </thead>
              <tbody>
                {rows.map((u) => (
                  <tr key={u.id} className="border-t">
                    <td className="p-3 font-semibold">{u.full_name}</td>
                    <td className="p-3 text-muted-foreground">{u.email}</td>
                    <td className="p-3">
                      <span className={`rounded px-2 py-0.5 text-xs font-bold ${
                        u.kyc_status === "verified" ? "bg-success/10 text-success" :
                        u.kyc_status === "pending"  ? "bg-warning/10 text-warning" :
                                                     "bg-muted text-muted-foreground"
                      }`}>{u.kyc_status}</span>
                    </td>
                    <td className="p-3">{u.is_active ? "نشط" : "موقوف"}</td>
                    <td className="p-3">
                      <button
                        onClick={async () => {
                          try {
                            u.is_active ? await adminApi.suspendUser(u.id) : await adminApi.activateUser(u.id);
                            toast.success("تم التحديث");
                            setRows((r) => r?.map((x) => x.id === u.id ? { ...x, is_active: !x.is_active } : x) ?? null);
                          } catch (e: any) { toast.error(e?.response?.data?.detail ?? "فشل"); }
                        }}
                        className="rounded bg-secondary px-3 py-1.5 text-xs font-semibold hover:bg-secondary/70"
                      >
                        {u.is_active ? "إيقاف" : "تفعيل"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
    </div>
  );
}

// ─────────────────────────────────────────── KYC ──────────────────────────
function KycTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  useEffect(() => {
    tryApi(() => adminApi.listKycRequests("pending").then((r) => r.data), [
      { id: "k1", user: { full_name: "أحمد", email: "a@x.com" }, id_front_url: "https://placehold.co/400x250", selfie_url: "https://placehold.co/400x400" },
    ]).then(setRows);
  }, []);

  async function decide(id: string, decision: "approved" | "rejected", note = "") {
    try {
      await adminApi.reviewKyc(id, decision, note);
      toast.success(decision === "approved" ? "تم توثيق الهوية" : "تم رفض التحقق");
      setRows((r) => r?.filter((x) => x.id !== id) ?? null);
    } catch (e: any) { toast.error(e?.response?.data?.detail ?? "فشل"); }
  }

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">طلبات التحقق (KYC)</h1>
      {rows == null ? <LoadingBlock /> :
        rows.length === 0 ? <EmptyBlock label="لا توجد طلبات معلّقة" /> : (
          <div className="space-y-4">
            {rows.map((r) => (
              <div key={r.id} className="rounded-xl border bg-card p-5">
                <div className="flex flex-col gap-4 lg:flex-row">
                  <div className="flex gap-2">
                    {r.id_front_url && <img src={r.id_front_url} className="h-40 rounded-lg object-cover" alt="ID" />}
                    {r.selfie_url   && <img src={r.selfie_url}   className="h-40 rounded-lg object-cover" alt="Selfie" />}
                  </div>
                  <div className="flex-1">
                    <div className="font-bold">{r.user?.full_name ?? "—"}</div>
                    <div className="text-sm text-muted-foreground">{r.user?.email}</div>
                    <div className="mt-6 flex gap-2">
                      <button onClick={() => decide(r.id, "approved")} className="rounded-lg bg-success px-4 py-2 text-sm font-bold text-white">قبول</button>
                      <button onClick={() => decide(r.id, "rejected", "المستندات غير واضحة")} className="rounded-lg bg-destructive px-4 py-2 text-sm font-bold text-white">رفض</button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

// ─────────────────────────────────────────── Admins (super_admin) ─────────
function AdminsTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  const [form, setForm] = useState({ user_id: "", role: "reviewer" });

  async function load() {
    const data = await tryApi(() => adminApi.listAdmins().then((r) => r.data), [
      { id: "a1", user: { full_name: "Super Admin", email: "admin@moamalati.com" }, role: "super_admin", is_active: true },
    ]);
    setRows(data);
  }
  useEffect(() => { load(); }, []);

  async function create() {
    if (!form.user_id) { toast.error("أدخل معرّف المستخدم"); return; }
    try {
      await adminApi.createAdmin(form);
      toast.success("تمت إضافة المشرف");
      setForm({ user_id: "", role: "reviewer" });
      load();
    } catch (e: any) { toast.error(e?.response?.data?.detail ?? "فشل"); }
  }

  const ROLES = ["super_admin", "admin", "moderator", "reviewer"];
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">إدارة المشرفين</h1>

      <div className="mb-6 rounded-xl border bg-card p-5">
        <h2 className="mb-3 font-bold">إضافة مشرف</h2>
        <div className="grid gap-3 sm:grid-cols-[1fr_180px_120px]">
          <input value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })} placeholder="user_id (UUID)" className="rounded-lg border bg-background px-3 py-2 text-sm" />
          <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="rounded-lg border bg-background px-3 py-2 text-sm">
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
          <button onClick={create} className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground">إضافة</button>
        </div>
      </div>

      {rows == null ? <LoadingBlock /> :
        <div className="overflow-hidden rounded-xl border bg-card">
          <table className="w-full text-sm">
            <thead className="bg-secondary text-right"><tr><th className="p-3">المشرف</th><th className="p-3">الدور</th><th className="p-3">الحالة</th><th className="p-3">إجراء</th></tr></thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id} className="border-t">
                  <td className="p-3">
                    <div className="font-semibold">{a.user?.full_name ?? a.user_id}</div>
                    <div className="text-xs text-muted-foreground">{a.user?.email}</div>
                  </td>
                  <td className="p-3">
                    <select
                      defaultValue={a.role}
                      onChange={async (e) => {
                        try { await adminApi.updateAdmin(a.id, { role: e.target.value }); toast.success("تم التحديث"); }
                        catch (er: any) { toast.error(er?.response?.data?.detail ?? "فشل"); }
                      }}
                      className="rounded border bg-background px-2 py-1 text-xs"
                    >
                      {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
                    </select>
                  </td>
                  <td className="p-3">{a.is_active ? "نشط" : "معطّل"}</td>
                  <td className="p-3">
                    <button
                      onClick={async () => {
                        if (!confirm("حذف المشرف؟")) return;
                        try { await adminApi.deleteAdmin(a.id); toast.success("تم الحذف"); load(); }
                        catch (er: any) { toast.error(er?.response?.data?.detail ?? "فشل"); }
                      }}
                      className="rounded bg-destructive/10 px-3 py-1 text-xs font-semibold text-destructive"
                    >حذف</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      }
    </div>
  );
}

// ─────────────────────────────────────────── Logs ─────────────────────────
function LogsTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  useEffect(() => {
    tryApi(() => adminApi.getActionsLog(1).then((r) => r.data), [
      { id: "l1", admin: { full_name: "Super Admin" }, action_type: "listing.approve", target_id: "abc", created_at: new Date().toISOString() },
    ]).then(setRows);
  }, []);
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">سجل الإجراءات</h1>
      {rows == null ? <LoadingBlock /> :
        rows.length === 0 ? <EmptyBlock label="لا توجد إجراءات" /> :
        <div className="overflow-hidden rounded-xl border bg-card">
          <table className="w-full text-sm">
            <thead className="bg-secondary text-right"><tr><th className="p-3">المشرف</th><th className="p-3">الإجراء</th><th className="p-3">الهدف</th><th className="p-3">التاريخ</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="p-3">{r.admin?.full_name ?? r.admin_id}</td>
                  <td className="p-3 font-mono text-xs">{r.action_type}</td>
                  <td className="p-3 font-mono text-xs">{r.target_id ?? "—"}</td>
                  <td className="p-3 text-muted-foreground">{new Date(r.created_at).toLocaleString("ar-EG")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      }
    </div>
  );
}

// ─────────────────────────────────────────── Reports ──────────────────────
function ReportsTab() {
  const [rows, setRows] = useState<any[] | null>(null);
  useEffect(() => {
    tryApi(() => adminApi.listReports("open").then((r) => r.data), []).then(setRows);
  }, []);
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">البلاغات</h1>
      {rows == null ? <LoadingBlock /> :
        rows.length === 0 ? <EmptyBlock label="لا توجد بلاغات مفتوحة" /> :
        <div className="space-y-3">
          {rows.map((r) => (
            <div key={r.id} className="rounded-xl border bg-card p-4">
              <div className="font-bold">{r.reason}</div>
              <div className="text-sm text-muted-foreground">{r.details}</div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={async () => { try { await adminApi.resolveReport(r.id, "handled"); toast.success("تم الحل"); setRows((x) => x?.filter((y) => y.id !== r.id) ?? null); } catch (e: any) { toast.error(e?.response?.data?.detail ?? "فشل"); } }}
                  className="rounded bg-success px-3 py-1.5 text-xs font-bold text-white"
                >معالجة</button>
              </div>
            </div>
          ))}
        </div>
      }
    </div>
  );
}

// ─────────────────────────────────────────── Settings ─────────────────────
const DEFAULT_PRICE_CAPS = {
  house: {
    sale: { excellent: 8_000_000, good: 5_000_000, poor: 2_500_000 },
    rent: { excellent: 80_000, good: 50_000, poor: 25_000 },
  },
  car: {
    sale: { excellent: 3_000_000, good: 1_800_000, poor: 900_000 },
    rent: { excellent: 15_000, good: 10_000, poor: 5_000 },
  },
};

type Banner = { title: string; image_url: string; link_url: string };

function SettingsTab() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);

  const [maintenance, setMaintenance] = useState(false);
  const [minImages, setMinImages] = useState(3);
  const [commission, setCommission] = useState(0);
  const [priceCaps, setPriceCaps] = useState<any>(DEFAULT_PRICE_CAPS);
  const [banners, setBanners] = useState<Banner[]>([]);
  const [featuredIds, setFeaturedIds] = useState("");

  useEffect(() => {
    tryApi(() => adminApi.getSettings().then((r) => r.data), {}).then((s: any) => {
      setMaintenance(!!s.maintenance_mode);
      setMinImages(s.min_listing_images ?? 3);
      setCommission(s.commission_rate ?? 0);
      setPriceCaps(s.price_caps ?? DEFAULT_PRICE_CAPS);
      setBanners(s.homepage_content?.banners ?? []);
      setFeaturedIds((s.homepage_content?.featured_listing_ids ?? []).join(", "));
      setLoading(false);
    });
  }, []);

  async function save(key: string, value: any, label: string) {
    setSaving(key);
    try {
      await adminApi.updateSetting(key, value);
      toast.success(`تم حفظ ${label}`);
    } catch {
      toast.error("تعذّر الحفظ");
    } finally {
      setSaving(null);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">إعدادات النظام</h1>

      {/* وضع الصيانة */}
      <div className="rounded-xl border bg-card p-5">
        <div className="flex items-center justify-between">
          <div>
            <div className="font-bold">وضع الصيانة</div>
            <div className="text-sm text-muted-foreground">
              عند التفعيل، يُغلق الموقع بالكامل أمام الزوار (ما عدا تسجيل الدخول ولوحة الإدارة).
            </div>
          </div>
          <button
            onClick={() => {
              const next = !maintenance;
              setMaintenance(next);
              save("maintenance_mode", next, "وضع الصيانة");
            }}
            className={`relative h-7 w-14 rounded-full transition ${maintenance ? "bg-destructive" : "bg-secondary"}`}
          >
            <span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition-all ${maintenance ? "right-1" : "right-8"}`} />
          </button>
        </div>
      </div>

      {/* حد أدنى الصور + العمولة */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border bg-card p-5">
          <div className="font-bold">الحد الأدنى لصور الإعلان</div>
          <div className="mt-3 flex gap-2">
            <input
              type="number" min={1} max={20} value={minImages}
              onChange={(e) => setMinImages(Number(e.target.value))}
              className="w-24 rounded-lg border bg-background p-2 text-center"
            />
            <button
              disabled={saving === "min_listing_images"}
              onClick={() => save("min_listing_images", minImages, "الحد الأدنى للصور")}
              className="rounded-lg bg-primary px-4 text-sm font-bold text-primary-foreground disabled:opacity-60"
            >
              حفظ
            </button>
          </div>
        </div>

        <div className="rounded-xl border bg-card p-5">
          <div className="font-bold">نسبة العمولة (%)</div>
          <div className="mt-3 flex gap-2">
            <input
              type="number" min={0} max={100} step={0.5} value={commission}
              onChange={(e) => setCommission(Number(e.target.value))}
              className="w-24 rounded-lg border bg-background p-2 text-center"
            />
            <button
              disabled={saving === "commission_rate"}
              onClick={() => save("commission_rate", commission, "نسبة العمولة")}
              className="rounded-lg bg-primary px-4 text-sm font-bold text-primary-foreground disabled:opacity-60"
            >
              حفظ
            </button>
          </div>
        </div>
      </div>

      {/* سقوف الأسعار */}
      <div className="rounded-xl border bg-card p-5">
        <div className="mb-3 font-bold">سقوف الأسعار حسب الفئة والحالة (جنيه)</div>
        {(["house", "car"] as const).map((cat) => (
          <div key={cat} className="mb-4">
            <div className="mb-2 text-sm font-semibold text-muted-foreground">
              {cat === "house" ? "عقارات" : "سيارات"}
            </div>
            {(["sale", "rent"] as const).map((type) => (
              <div key={type} className="mb-2 grid grid-cols-4 items-center gap-2 text-sm">
                <span>{type === "sale" ? "بيع" : "إيجار"}</span>
                {(["excellent", "good", "poor"] as const).map((grade) => (
                  <input
                    key={grade}
                    type="number"
                    value={priceCaps?.[cat]?.[type]?.[grade] ?? 0}
                    placeholder={grade}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setPriceCaps((prev: any) => ({
                        ...prev,
                        [cat]: { ...prev[cat], [type]: { ...prev[cat][type], [grade]: v } },
                      }));
                    }}
                    className="rounded-lg border bg-background p-2 text-center"
                  />
                ))}
              </div>
            ))}
          </div>
        ))}
        <button
          disabled={saving === "price_caps"}
          onClick={() => save("price_caps", priceCaps, "سقوف الأسعار")}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-60"
        >
          حفظ سقوف الأسعار
        </button>
      </div>

      {/* محتوى الصفحة الرئيسية */}
      <div className="rounded-xl border bg-card p-5">
        <div className="mb-3 font-bold">محتوى الصفحة الرئيسية</div>

        <div className="space-y-2">
          {banners.map((b, i) => (
            <div key={i} className="grid grid-cols-[1fr_1fr_1fr_auto] gap-2">
              <input
                placeholder="العنوان" value={b.title}
                onChange={(e) => setBanners((prev) => prev.map((x, j) => (j === i ? { ...x, title: e.target.value } : x)))}
                className="rounded-lg border bg-background p-2 text-sm"
              />
              <input
                placeholder="رابط الصورة" value={b.image_url}
                onChange={(e) => setBanners((prev) => prev.map((x, j) => (j === i ? { ...x, image_url: e.target.value } : x)))}
                className="rounded-lg border bg-background p-2 text-sm"
              />
              <input
                placeholder="رابط الانتقال" value={b.link_url}
                onChange={(e) => setBanners((prev) => prev.map((x, j) => (j === i ? { ...x, link_url: e.target.value } : x)))}
                className="rounded-lg border bg-background p-2 text-sm"
              />
              <button onClick={() => setBanners((prev) => prev.filter((_, j) => j !== i))} className="rounded-lg border border-destructive/30 px-2 text-destructive">
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          ))}
          <button
            onClick={() => setBanners((prev) => [...prev, { title: "", image_url: "", link_url: "" }])}
            className="flex items-center gap-1 text-sm font-semibold text-primary"
          >
            <Plus className="h-4 w-4" /> إضافة بانر
          </button>
        </div>

        <div className="mt-4">
          <label className="text-sm font-semibold">معرّفات الإعلانات المميزة (مفصولة بفاصلة)</label>
          <input
            value={featuredIds}
            onChange={(e) => setFeaturedIds(e.target.value)}
            className="mt-1 w-full rounded-lg border bg-background p-2 text-sm"
            placeholder="id1, id2, id3"
          />
        </div>

        <button
          disabled={saving === "homepage_content"}
          onClick={() =>
            save(
              "homepage_content",
              { banners, featured_listing_ids: featuredIds.split(",").map((s) => s.trim()).filter(Boolean) },
              "محتوى الصفحة الرئيسية",
            )
          }
          className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-60"
        >
          حفظ محتوى الرئيسية
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── الفئات ───────────────────────
function CategoriesTab() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    tryApi(() => adminApi.listCategories().then((r) => r.data), []).then((d: any) => {
      setItems(d);
      setLoading(false);
    });
  }
  useEffect(load, []);

  async function update(id: string, patch: any) {
    setItems((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
    try {
      await adminApi.updateCategory(id, patch);
      toast.success("تم الحفظ");
    } catch {
      toast.error("تعذّر الحفظ");
      load();
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div>
      <h1 className="mb-2 text-3xl font-bold">الفئات والأسعار</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        تعديل اسم/أيقونة/تفعيل/ترتيب الفئات الحالية. إضافة فئة جديدة كلياً (غير عقارات/سيارات) تتطلب تعديل
        على نموذج الذكاء الاصطناعي وبنية قاعدة البيانات، وليست جزءاً من هذا القسم.
      </p>
      {items.length === 0 && <EmptyBlock label="لا توجد فئات — تأكد من استيراد maskan_mysql.sql" />}
      <div className="space-y-3">
        {items.map((c) => (
          <div key={c.id} className="grid grid-cols-[1fr_1fr_1fr_auto_auto] items-center gap-3 rounded-xl border bg-card p-4">
            <input
              defaultValue={c.name_ar}
              onBlur={(e) => e.target.value !== c.name_ar && update(c.id, { name_ar: e.target.value })}
              className="rounded-lg border bg-background p-2 text-sm"
            />
            <input
              defaultValue={c.name_en ?? ""}
              onBlur={(e) => e.target.value !== c.name_en && update(c.id, { name_en: e.target.value })}
              className="rounded-lg border bg-background p-2 text-sm"
              placeholder="English name"
            />
            <input
              defaultValue={c.icon ?? ""}
              onBlur={(e) => e.target.value !== c.icon && update(c.id, { icon: e.target.value })}
              className="rounded-lg border bg-background p-2 text-sm"
              placeholder="اسم الأيقونة"
            />
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={!!c.is_active} onChange={(e) => update(c.id, { is_active: e.target.checked })} />
              مفعّلة
            </label>
            <input
              type="number" defaultValue={c.sort_order}
              onBlur={(e) => Number(e.target.value) !== c.sort_order && update(c.id, { sort_order: Number(e.target.value) })}
              className="w-20 rounded-lg border bg-background p-2 text-center text-sm"
            />
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── التحليلات ────────────────────
function AnalyticsTab() {
  const [data, setData] = useState<any>(null);
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    tryApi(() => adminApi.getAnalytics(days).then((r) => r.data), null).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [days]);

  if (loading || !data) return <LoadingBlock />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">التحليلات</h1>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))} className="rounded-lg border bg-card p-2 text-sm">
          <option value={7}>آخر 7 أيام</option>
          <option value={30}>آخر 30 يوماً</option>
          <option value={90}>آخر 90 يوماً</option>
        </select>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border bg-card p-4">
          <div className="mb-3 font-bold">تسجيلات مستخدمين جدد</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.signups}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <div className="mb-3 font-bold">إعلانات جديدة مقابل منشورة</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={data.new_listings}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line name="جديدة" type="monotone" dataKey="count" stroke="hsl(var(--primary))" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <div className="mb-3 font-bold">الإعلانات حسب الفئة</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_category}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="category" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="hsl(var(--primary))" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="rounded-xl border bg-card p-4">
          <div className="mb-3 font-bold">أكثر 10 مدن نشاطاً</div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_city} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="city" type="category" width={80} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="hsl(var(--primary))" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── إشعار جماعي ──────────────────
function BroadcastTab() {
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [audience, setAudience] = useState("all");
  const [sending, setSending] = useState(false);

  async function send() {
    if (!title.trim() || !body.trim()) {
      toast.error("اكتب العنوان والنص");
      return;
    }
    setSending(true);
    try {
      const res = await adminApi.broadcast({ title, body, audience });
      toast.success(`تم الإرسال إلى ${res.data.sent_to} مستخدم`);
      setTitle("");
      setBody("");
    } catch {
      toast.error("تعذّر إرسال الإشعار");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-6 text-3xl font-bold">إشعار جماعي</h1>
      <div className="space-y-4 rounded-xl border bg-card p-5">
        <div>
          <label className="text-sm font-semibold">الفئة المستهدفة</label>
          <select value={audience} onChange={(e) => setAudience(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2 text-sm">
            <option value="all">الجميع</option>
            <option value="buyer">المشترون فقط</option>
            <option value="seller">البائعون فقط</option>
            <option value="both">بائع ومشترٍ</option>
          </select>
        </div>
        <div>
          <label className="text-sm font-semibold">العنوان</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2 text-sm" />
        </div>
        <div>
          <label className="text-sm font-semibold">النص</label>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={4} className="mt-1 w-full rounded-lg border bg-background p-2 text-sm" />
        </div>
        <button
          disabled={sending}
          onClick={send}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2.5 font-bold text-primary-foreground disabled:opacity-60"
        >
          {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Megaphone className="h-4 w-4" />}
          إرسال
        </button>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────── Helpers ──────────────────────
function LoadingBlock() {
  return <div className="flex items-center justify-center rounded-xl border bg-card p-10 text-muted-foreground"><Loader2 className="h-6 w-6 animate-spin" /></div>;
}
function EmptyBlock({ label }: { label: string }) {
  return <div className="rounded-xl border bg-card p-10 text-center text-muted-foreground">{label}</div>;
}