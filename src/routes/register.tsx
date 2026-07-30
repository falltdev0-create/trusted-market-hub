import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Shield, BadgeCheck, Bot, FileCheck2 } from "lucide-react";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "إنشاء حساب — مسكن" }] }),
  component: Register,
});

function passwordStrength(p: string) {
  let s = 0;
  if (p.length >= 8) s++;
  if (/[A-Z]/.test(p)) s++;
  if (/[0-9]/.test(p)) s++;
  if (/[^A-Za-z0-9]/.test(p)) s++;
  return s;
}

function Register() {
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirm: "",
  });
  const [loading, setLoading] = useState(false);
  const strength = passwordStrength(form.password);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (form.password !== form.confirm) {
      toast.error("كلمتا المرور غير متطابقتين");
      return;
    }
    if (strength < 3) {
      toast.error("كلمة المرور ضعيفة");
      return;
    }
    setLoading(true);
    try {
      const response = await authApi.register({
        full_name: form.name,
        email: form.email,
        phone: form.phone,
        password: form.password,
      });
      const data = response.data;
      login(
        { id: data.user_id, name: data.full_name, email: form.email, role: "user", admin_role: null },
        data.access_token,
      );
      toast.success("تم إنشاء الحساب بنجاح");
      navigate({ to: "/dashboard" });
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || "فشل إنشاء الحساب");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid min-h-[calc(100vh-4rem)] grid-cols-1 lg:grid-cols-2">
      <div className="hidden bg-gradient-to-bl from-primary to-primary-light p-12 text-primary-foreground lg:flex lg:flex-col lg:justify-center">
        <Shield className="h-12 w-12" />
        <h2 className="mt-6 text-4xl font-extrabold">انضم لمنصة مسكن</h2>
        <p className="mt-3 max-w-md text-white/90">
          مجتمع موثّق من البائعين والمشترين. كل صفقة محمية وكل بائع موثّق بهويته.
        </p>
        <ul className="mt-10 space-y-4">
          {[
            { i: BadgeCheck, t: "تحقق فوري من الهوية الوطنية" },
            { i: Bot, t: "تقييم ذكي لحالة السلعة" },
            { i: FileCheck2, t: "حماية مستندات الملكية" },
          ].map((f) => (
            <li key={f.t} className="flex items-center gap-3">
              <div className="rounded-lg bg-white/10 p-2 backdrop-blur">
                <f.i className="h-5 w-5" />
              </div>
              <span>{f.t}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex items-center justify-center p-6 sm:p-12">
        <form onSubmit={handleSubmit} className="w-full max-w-md space-y-5">
          <div>
            <h1 className="text-3xl font-bold">إنشاء حساب جديد</h1>
            <p className="mt-1 text-sm text-muted-foreground">ابدأ رحلتك في مسكن</p>
          </div>

          {(
            [
              { k: "name", l: "الاسم الكامل", t: "text" },
              { k: "email", l: "البريد الإلكتروني", t: "email" },
              { k: "phone", l: "رقم الهاتف", t: "tel" },
            ] as const
          ).map((f) => (
            <div key={f.k}>
              <label className="mb-1.5 block text-sm font-semibold">{f.l}</label>
              <input
                type={f.t}
                required
                value={(form as any)[f.k]}
                onChange={(e) => setForm({ ...form, [f.k]: e.target.value })}
                className="w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
              />
            </div>
          ))}

          <div>
            <label className="mb-1.5 block text-sm font-semibold">كلمة المرور</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
            {form.password && (
              <div className="mt-2 flex gap-1">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className={`h-1.5 flex-1 rounded ${
                      i <= strength
                        ? strength <= 2
                          ? "bg-destructive"
                          : strength === 3
                            ? "bg-warning"
                            : "bg-success"
                        : "bg-secondary"
                    }`}
                  />
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-semibold">تأكيد كلمة المرور</label>
            <input
              type="password"
              required
              value={form.confirm}
              onChange={(e) => setForm({ ...form, confirm: e.target.value })}
              className="w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>

          <button
            disabled={loading}
            className="w-full rounded-lg bg-primary py-3 font-bold text-primary-foreground transition hover:bg-primary-light disabled:opacity-60"
          >
            {loading ? "جاري الإنشاء..." : "إنشاء الحساب"}
          </button>

          <p className="text-center text-sm text-muted-foreground">
            لديك حساب بالفعل؟{" "}
            <Link to="/login" className="font-semibold text-primary hover:underline">
              تسجيل الدخول
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
