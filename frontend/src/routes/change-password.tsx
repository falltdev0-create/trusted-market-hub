// src/routes/change-password.tsx

import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Eye, EyeOff } from "lucide-react";

import { usersApi } from "@/lib/api";
import { useLanguage } from "@/i18n/LanguageContext";

export const Route = createFileRoute("/change-password")({
  component: ChangePasswordPage,
});

function ChangePasswordPage() {
  const { t } = useLanguage();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const handleSubmit = async () => {
    if (!currentPassword.trim()) {
      toast.error(t("password.enterCurrent"));
      return;
    }

    if (!newPassword.trim()) {
      toast.error(t("password.enterNew"));
      return;
    }

    if (newPassword !== confirmPassword) {
      toast.error(t("messages.passwordMismatch"));
      return;
    }

    if (newPassword.length < 8) {
      toast.error(t("password.minimum"));
      return;
    }

    try {
      setLoading(true);

      await usersApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      toast.success(t("messages.passwordChanged"));

      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

    } catch (error: any) {
      toast.error(
        error.response?.data?.detail ??
        t("messages.saveError")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
        onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
        }}
        className="mx-auto max-w-md p-6">
        
      <h1 className="mb-6 text-2xl font-bold">
        {t("password.title")}
      </h1>

      <div className="relative">
  <input
            type={showCurrentPassword ? "text" : "password"}
            placeholder={t("password.current")}
            className="w-full rounded-lg border p-3 pr-10"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
        />

        <button
            type="button"
            onClick={() => setShowCurrentPassword(!showCurrentPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
        >
            {showCurrentPassword ? (
            <EyeOff className="h-5 w-5" />
            ) : (
            <Eye className="h-5 w-5" />
            )}
        </button>
        </div>
        <div className="relative">
            <input
        type={showNewPassword ? "text" : "password"}
        placeholder={t("password.new")}
        className="w-full rounded-lg border p-3 pr-10"
        value={newPassword}
        onChange={(e) => setNewPassword(e.target.value)}
    />

    <button
        type="button"
        onClick={() => setShowNewPassword(!showNewPassword)}
        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
    >
        {showNewPassword ? (
        <EyeOff className="h-5 w-5" />
        ) : (
        <Eye className="h-5 w-5" />
        )}
    </button>
    </div>
<div className="relative">
  <input
    type={showConfirmPassword ? "text" : "password"}
    placeholder={t("password.confirmNew")}
    className="w-full rounded-lg border p-3 pr-10"
    value={confirmPassword}
    onChange={(e) => setConfirmPassword(e.target.value)}
  />

  <button
    type="button"
    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
  >
    {showConfirmPassword ? (
      <EyeOff className="h-5 w-5" />
    ) : (
      <Eye className="h-5 w-5" />
    )}
  </button>
</div>

        <button
  type="submit"
  disabled={loading}
  className="h-10 w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
>
  {loading ? t("password.saving") : t("common.save")}
</button>
      </form>
  );
}