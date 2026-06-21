import { createFileRoute } from "@tanstack/react-router";

import {
  Lock,
  Languages,
  FileText,
  Shield,
  Trash2,
  ChevronLeft,
} from "lucide-react";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">الإعدادات</h1>

      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">

        <button className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5" />
            <span>تغيير كلمة المرور</span>
          </div>
          <ChevronLeft className="h-5 w-5" />
        </button>

        <button className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50">
          <div className="flex items-center gap-3">
            <Languages className="h-5 w-5" />
            <span>اللغة</span>
          </div>
          <ChevronLeft className="h-5 w-5" />
        </button>

        <button className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50">
          <div className="flex items-center gap-3">
            <FileText className="h-5 w-5" />
            <span>الشروط والأحكام</span>
          </div>
          <ChevronLeft className="h-5 w-5" />
        </button>

        <button className="flex w-full items-center justify-between border-b px-5 py-4 transition hover:bg-muted/50">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5" />
            <span>سياسة الخصوصية</span>
          </div>
          <ChevronLeft className="h-5 w-5" />
        </button>

        <button className="flex w-full items-center justify-between px-5 py-4 text-red-500 transition hover:bg-red-50 dark:hover:bg-red-950/20">
          <div className="flex items-center gap-3">
            <Trash2 className="h-5 w-5" />
            <span>حذف الحساب</span>
          </div>
          <ChevronLeft className="h-5 w-5" />
        </button>

      </div>
    </div>
  );
}