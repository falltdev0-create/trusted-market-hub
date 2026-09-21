// src/routes/login.tsx
import { createFileRoute, useNavigate, Link } from "@tanstack/react-router";
import { useState } from "react";
import { Shield } from "lucide-react";
import { toast } from "sonner";
import { authApi } from "@/lib/api";
import { useAuthStore } from "@/stores/auth";
import { useLanguage } from "@/i18n/LanguageContext";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "تسجيل الدخول — مسكن" }] }),
  component: Login,
});

function Login() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await authApi.login(email, password);
      const data = response.data;
      login(
        {
          id: data.user_id,
          name: data.full_name,
          email,
          role: data.admin_role ? "admin" : "user",
          admin_role: data.admin_role ?? null,
        },
        data.access_token,
      );
      toast.success(t("messages.loginSuccess"));
      navigate({ to: "/dashboard" });
    } catch {
      toast.error(t("messages.invalidCredentials"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-md rounded-2xl border bg-card p-8 shadow-[var(--shadow-card)]">
        <div className="mb-6 text-center">
          <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10">
            <Shield className="h-7 w-7 text-primary" />
          </div>
          <h1 className="mt-4 text-2xl font-bold">{t("auth.welcomeBack")}</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t("auth.loginSubtitle")}</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-sm font-semibold">{t("auth.email")}</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <label className="text-sm font-semibold">{t("auth.password")}</label>
              <a href="#" className="text-xs text-primary hover:underline">
                {t("auth.forgotPassword")}
              </a>
            </div>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border bg-card px-4 py-2.5 outline-none focus:border-primary focus:ring-2 focus:ring-primary/20"
            />
          </div>
          <button
            disabled={loading}
            className="w-full rounded-lg bg-primary py-3 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-60"
          >
            {loading ? t("auth.loggingIn") : t("navigation.login")}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
          <div className="h-px flex-1 bg-border" /> {t("auth.or")} <div className="h-px flex-1 bg-border" />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <button className="rounded-lg border bg-card py-2.5 text-sm font-semibold hover:bg-secondary">
            Google
          </button>
          <button className="rounded-lg border bg-card py-2.5 text-sm font-semibold hover:bg-secondary">
            Apple
          </button>
        </div>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          {t("auth.noAccount")} {" "}
          <Link to="/register" className="font-semibold text-primary hover:underline">
            {t("navigation.register")}
          </Link>
        </p>
      </div>
    </div>
  );
}