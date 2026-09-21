// src/routes/verification.tsx
// kyc verification page

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Upload, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { usersApi } from "@/lib/api";
import { useLanguage } from "@/i18n/LanguageContext";

export const Route = createFileRoute("/verification")({
  component: VerificationPage,
});

function VerificationPage() {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const [idDocument, setIdDocument] = useState<File | null>(null);
  const [selfie, setSelfie] = useState<File | null>(null);

  const submitKYC = useMutation({
    mutationFn: async () => {
      if (!idDocument || !selfie) {
        throw new Error(t("verification.missingFiles"));
      }

      const formData = new FormData();
      formData.append("id_document", idDocument);
      formData.append("selfie", selfie);

      return usersApi.submitKYC(formData);
    },

    onSuccess: () => {
      toast.success(t("verification.submitted"));

      navigate({
        to: "/dashboard",
      });
    },

    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail ??
          error?.message ??
          t("verification.submitFailed")
      );
    },
  });

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-8 flex items-center gap-3">
        <ShieldCheck className="h-8 w-8 text-primary" />

        <div>
          <h1 className="text-2xl font-bold">
            {t("verification.title")}
          </h1>

          <p className="text-sm text-muted-foreground">
            {t("verification.description")}
          </p>
        </div>
      </div>

      <div className="rounded-2xl border bg-card p-6 shadow-sm">

        {/* صورة الهوية */}
        <label className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition hover:border-primary hover:bg-muted">
          <Upload className="mb-3 h-10 w-10 text-primary" />

          <span className="font-medium">
            {t("verification.identityUpload")}
          </span>

          <span className="mt-1 text-sm text-muted-foreground">
            JPG - PNG - PDF
          </span>

          <input
            type="file"
            accept="image/*,.pdf"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.length) {
                setIdDocument(e.target.files[0]);
              }
            }}
          />
        </label>

        {idDocument && (
          <div className="mb-5 rounded-lg bg-muted p-3 text-sm">
            <span className="font-medium">
              {t("verification.selectedIdentity")}
            </span>{" "}
            {idDocument.name}
          </div>
        )}

        {/* صورة السيلفي */}
        <label className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition hover:border-primary hover:bg-muted">
          <Upload className="mb-3 h-10 w-10 text-primary" />

          <span className="font-medium">
            {t("verification.selfieUpload")}
          </span>

          <span className="mt-1 text-sm text-muted-foreground">
            JPG - PNG
          </span>

          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.length) {
                setSelfie(e.target.files[0]);
              }
            }}
          />
        </label>

        {selfie && (
          <div className="mb-5 rounded-lg bg-muted p-3 text-sm">
            <span className="font-medium">
              {t("verification.selectedSelfie")}
            </span>{" "}
            {selfie.name}
          </div>
        )}

        <button
          disabled={
            !idDocument ||
            !selfie ||
            submitKYC.isPending
          }
          onClick={() => submitKYC.mutate()}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-5 py-3 font-medium text-primary-foreground transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitKYC.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t("verification.submitting")}
            </>
          ) : (
            <>
              <ShieldCheck className="h-4 w-4" />
              {t("verification.submit")}
            </>
          )}
        </button>

      </div>
    </div>
  );
}