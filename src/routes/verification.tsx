// src/routes/verification.tsx

import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Upload, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

import { usersApi } from "@/lib/api";

export const Route = createFileRoute("/verification")({
  component: VerificationPage,
});

function VerificationPage() {
  const navigate = useNavigate();

  const [idDocument, setIdDocument] = useState<File | null>(null);
  const [selfie, setSelfie] = useState<File | null>(null);

  const submitKYC = useMutation({
    mutationFn: async () => {
      if (!idDocument || !selfie) {
        throw new Error("يرجى رفع صورة الهوية وصورة السيلفي.");
      }

      const formData = new FormData();
      formData.append("id_document", idDocument);
      formData.append("selfie", selfie);

      return usersApi.submitKYC(formData);
    },

    onSuccess: () => {
      toast.success("تم إرسال طلب التحقق بنجاح.");

      navigate({
        to: "/dashboard",
      });
    },

    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail ??
          error?.message ??
          "تعذر إرسال الطلب."
      );
    },
  });

  return (
    <div className="mx-auto max-w-2xl p-6">
      <div className="mb-8 flex items-center gap-3">
        <ShieldCheck className="h-8 w-8 text-primary" />

        <div>
          <h1 className="text-2xl font-bold">
            التحقق من الهوية
          </h1>

          <p className="text-sm text-muted-foreground">
            ارفع صورة الهوية الوطنية أو جواز السفر وصورة السيلفي لإرسالها للمراجعة.
          </p>
        </div>
      </div>

      <div className="rounded-2xl border bg-card p-6 shadow-sm">

        {/* صورة الهوية */}
        <label className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition hover:border-primary hover:bg-muted">
          <Upload className="mb-3 h-10 w-10 text-primary" />

          <span className="font-medium">
            ارفع صورة الهوية أو جواز السفر
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
              الهوية المختارة:
            </span>{" "}
            {idDocument.name}
          </div>
        )}

        {/* صورة السيلفي */}
        <label className="mb-4 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition hover:border-primary hover:bg-muted">
          <Upload className="mb-3 h-10 w-10 text-primary" />

          <span className="font-medium">
            ارفع صورة السيلفي
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
              السيلفي المختار:
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
              جارٍ الإرسال...
            </>
          ) : (
            <>
              <ShieldCheck className="h-4 w-4" />
              إرسال للمراجعة
            </>
          )}
        </button>

      </div>
    </div>
  );
}