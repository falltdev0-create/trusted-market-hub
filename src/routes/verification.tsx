// src/routes/verification.tsx

import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/verification")({
  component: VerificationPage,
});

function VerificationPage() {
  return (
    <div className="mx-auto max-w-2xl p-6">
      <h1 className="mb-6 text-2xl font-bold">
        التحقق من الهوية
      </h1>

      <div className="rounded-xl border p-6">
        <p className="mb-4 text-muted-foreground">
          قم برفع صورة الهوية أو جواز السفر للتحقق من حسابك.
        </p>

        <input
          type="file"
          accept="image/*,.pdf"
          className="mb-4 w-full"
        />

        <button className="rounded-lg bg-primary px-5 py-2 text-primary-foreground">
          إرسال للمراجعة
        </button>
      </div>
    </div>
  );
}