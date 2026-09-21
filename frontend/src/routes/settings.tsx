import { createFileRoute, useNavigate } from "@tanstack/react-router";

import {
  Lock,
  Languages,
  FileText,
  Shield,
  Trash2,
  ChevronLeft,
} from "lucide-react";

import { useLanguage } from "@/i18n/LanguageContext";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const navigate = useNavigate();

  const { language, setLanguage, t } = useLanguage();

  const toggleLanguage = () => {
    setLanguage(language === "ar" ? "en" : "ar");
  };

  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">
        {t("settings.title")}
      </h1>

      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">

        {/* Change Password */}
        <button
          type="button"
          onClick={() => navigate({ to: "/change-password" })}
          className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5" />
            <span>{t("settings.changePassword")}</span>
          </div>

          <ChevronLeft className="h-5 w-5" />
        </button>

        {/* Language */}
        <button
          type="button"
          onClick={toggleLanguage}
          className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <Languages className="h-5 w-5" />
            <span>{t("settings.language")}</span>
          </div>

          <span className="text-sm text-muted-foreground">
            {language === "ar"
              ? t("settings.arabic")
              : t("settings.english")}
          </span>
        </button>

        {/* Terms */}
        <button
          type="button"
          className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5" />
            <span>{t("settings.terms")}</span>
          </div>

          <ChevronLeft className="h-5 w-5" />
        </button>

        {/* Privacy */}
        <button
          type="button"
          className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50"
        >
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5" />
            <span>{t("settings.privacy")}</span>
          </div>

          <ChevronLeft className="h-5 w-5" />
        </button>

        {/* Delete Account */}
        <button
          type="button"
          className="flex w-full items-center justify-between px-5 py-4 text-red-500 transition hover:bg-red-50 dark:hover:bg-red-950/20"
        >
          <div className="flex items-center gap-3">
            <Trash2 className="h-5 w-5" />
            <span>{t("settings.deleteAccount")}</span>
          </div>

          <ChevronLeft className="h-5 w-5" />
        </button>

      </div>
    </div>
  );
}