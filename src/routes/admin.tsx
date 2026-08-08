import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard, ClipboardList, Users, ShieldCheck, UserCog,
  FileWarning, Settings2, History, Loader2, Check, X, Search,
} from "lucide-react";
import { toast } from "sonner";
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
  | "admins" | "logs" | "reports" | "settings";

const TABS: { id: Tab; label: string; icon: any; role: "any" | "super_admin" }[] = [
  { id: "dash",     label: "نظرة عامة",       icon: LayoutDashboard, role: "any" },
  { id: "listings", label: "الإعلانات",       icon: ClipboardList,   role: "any" },
  { id: "users",    label: "المستخدمون",      icon: Users,           role: "any" },
  { id: "kyc",      label: "طلبات التحقق",    icon: ShieldCheck,     role: "any" },
  { id: "admins",   label: "المشرفون",        icon: UserCog,         role: "super_admin" },
  { id: "logs",     label: "سجل الإجراءات",   icon: History,         role: "any" },
  { id: "reports",  label: "البلاغات",        icon: FileWarning,     role: "any" },
  { id: "settings", label: "الإعدادات",       icon: Settings2,       role: "super_admin" },
];

const ROLE_LABEL: Record<string, string> = {
  super_admin: "مدير عام (Super Admin)",
  admin: "مشرف (Admin)",
  moderator: "مُنسّق (Moderator)",
  reviewer: "مُراجع (Reviewer)",
};

function AdminPage() {
  const { user, isLoggedIn, login } = useAuthStore();
  const nav = useNavigate();
  const [tab, setTab] = useState<Tab>("dash");
  const [viewAs, setViewAs] = useState<string | null>(null);

  // الدور الحقيقي يأتي من الـ API؛ الواجهة تعكسه فقط والباكند يفرض التسلسل الهرمي.
  const realRole: string | null =
    (user as any)?.admin_role ??
    (user?.role === "super_admin" ? "super_admin" : user?.role === "admin" ? "admin" : null);
  const adminRole = viewAs ?? realRole;
  const isSuper = adminRole === "super_admin";
  const canSwitch = realRole === "super_admin";

  useEffect(() => {
    if (!isLoggedIn) nav({ to: "/login" });
  }, [isLoggedIn, nav]);

  // مزامنة الدور من الـ API عند فتح اللوحة
  useEffect(() => {
    if (!isLoggedIn) return;
    usersApi
      .me()
      .then((r) => {
        const me = r.data ?? {};
        const token = useAuthStore.getState().token ?? "";
        login(
          {
            id: String(me.id ?? user?.id ?? ""),
            name: me.full_name ?? user?.name ?? "",
            email: me.email ?? user?.email ?? "",
            role: me.role ?? user?.role,
            admin_role: me.admin_role ?? null,
          },
          token,
        );
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isLoggedIn]);

  useEffect(() => {
    if (viewAs && !canSwitch) setViewAs(null);
  }, [viewAs, canSwitch]);

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
              {adminRole ? (ROLE_LABEL[adminRole] ?? adminRole) : "مشرف"}
            </div>
            {canSwitch && (
              <button
                onClick={() => {
                  const next = isSuper ? "admin" : null;
                  setViewAs(next);
                  setTab("dash");
                  toast.info(next ? "تم التبديل إلى مسار المشرف" : "تم الرجوع لمسار المدير العام");
                }}
                className="mt-3 w-full rounded-lg border border-primary/30 bg-card px-2 py-1.5 text-xs font-bold text-primary transition hover:bg-primary/10"
              >
                {isSuper ? "عرض كمشرف عادي" : "العودة لصلاحيات المدير العام"}
              </button>
            )}
            {viewAs && (
              <div className="mt-2 rounded-md bg-warning/10 px-2 py-1 text-[11px] font-semibold text-warning">
                وضع معاينة — صلاحياتك الفعلية: مدير عام
              </div>
            )}
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
          {tab === "dash"     && <DashTab />}
          {tab === "listings" && <ListingsTab />}
          {tab === "users"    && <UsersTab />}
          {tab === "kyc"      && <KycTab />}
          {tab === "admins"   && <AdminsTab />}
          {tab === "logs"     && <LogsTab />}
          {tab === "reports"  && <ReportsTab />}
          {tab === "settings" && <SettingsTab />}
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
      { id: "a1", user: { full_name: "Super Admin", email: "admin@moamalati.local" }, role: "super_admin", is_active: true },
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
function SettingsTab() {
  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold">إعدادات النظام</h1>
      <div className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">
        إعدادات الحدود السعرية (رخيص/متوسط/غالي)، اسم الموقع، وإلزامية التحقق — تُدار من الـ backend
        <br />(<code className="font-mono">GET /admin/settings</code>).
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
