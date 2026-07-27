import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { FileText, Upload, ShieldCheck, Loader2, Info, Check } from "lucide-react";
import { toast } from "sonner";
import { StepProgress } from "@/components/StepProgress";
import { useListingStore } from "@/stores/listing";
import { verificationApi } from "@/lib/api";

export const Route = createFileRoute("/sell/upload-docs")({
  head: () => ({ meta: [{ title: "وثائق الملكية — مسكن" }] }),
  component: UploadDocs,
});

function UploadDocs() {
  const { draft, setDocs } = useListingStore();
  const [idFile, setIdFile] = useState<File | null>(null);
  const [ownFile, setOwnFile] = useState<File | null>(null);
  const [idDoc, setIdDoc] = useState<string | null>(null);
  const [ownDoc, setOwnDoc] = useState<string | null>(null);
  const [phase, setPhase] = useState<"idle" | "verifying" | "success" | "failed">("idle");
  const nav = useNavigate();

  async function submit() {
    if (!idDoc || !ownDoc) { toast.error("ارفع الوثيقتين أولاً"); return; }
    setPhase("verifying");
    try {
      if (draft.id && !draft.id.startsWith("local-") && idFile && ownFile) {
        const fd = new FormData();
        fd.append("id_document", idFile);
        fd.append("ownership_document", ownFile);
        await verificationApi.uploadDocs(draft.id, fd);
      } else {
        await new Promise((r) => setTimeout(r, 2200));
      }
      setPhase("success");
      setDocs(true, true, true);
      setTimeout(() => nav({ to: "/sell/details" }), 1200);
    } catch (e: any) {
      setPhase("failed");
      toast.error(e?.response?.data?.detail ?? "فشل التحقق من الوثائق");
      setTimeout(() => setPhase("idle"), 1500);
    }
  }

  if (phase === "verifying") {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="relative">
          <ShieldCheck className="h-20 w-20 animate-pulse text-primary" />
          <Loader2 className="absolute -bottom-2 -left-2 h-8 w-8 animate-spin text-accent" />
        </div>
        <h2 className="mt-6 text-2xl font-bold">جاري التحقق من الوثائق...</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          نقارن بياناتك مع وثيقة الملكية للتأكد من المطابقة.
        </p>
      </div>
    );
  }

  if (phase === "success") {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center px-4 py-20 text-center">
        <div className="inline-flex h-20 w-20 items-center justify-center rounded-full bg-success/10">
          <Check className="h-12 w-12 text-success" />
        </div>
        <h2 className="mt-6 text-2xl font-bold text-success">✅ تم التحقق بنجاح</h2>
        <p className="mt-2 text-sm text-muted-foreground">يتم تحويلك لإدخال بيانات الإعلان...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <StepProgress current={4} total={6} label="وثائق الملكية" />
      <h1 className="mb-2 text-3xl font-bold">رفع وثائق الملكية</h1>

      <div className="mb-6 flex items-start gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4 text-sm">
        <Info className="mt-0.5 h-5 w-5 flex-shrink-0 text-primary" />
        <p className="text-foreground">
          سيتحقق النظام من تطابق هويتك مع وثيقة الملكية — يُقبل القريب من الدرجة الأولى.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <DocUpload
          icon={FileText}
          title="بطاقة الهوية الوطنية"
          value={idDoc}
          onChange={(url, f) => { setIdDoc(url); setIdFile(f); }}
        />
        <DocUpload
          icon={ShieldCheck}
          title="وثيقة الملكية (عقد / استمارة)"
          value={ownDoc}
          onChange={(url, f) => { setOwnDoc(url); setOwnFile(f); }}
        />
      </div>

      <div className="mt-8 flex justify-end">
        <button
          onClick={submit}
          disabled={!idDoc || !ownDoc}
          className="rounded-lg bg-primary px-8 py-3 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
        >
          تحقق من الوثائق
        </button>
      </div>
    </div>
  );
}

function DocUpload({
  icon: Icon,
  title,
  value,
  onChange,
}: {
  icon: any;
  title: string;
  value: string | null;
  onChange: (v: string | null, f: File | null) => void;
}) {
  return (
    <label className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-card p-6 text-center transition hover:border-primary hover:bg-primary/5">
      {value ? (
        <img src={value} alt={title} className="mb-3 max-h-32 rounded" />
      ) : (
        <Icon className="mb-3 h-10 w-10 text-primary" />
      )}
      <p className="font-semibold">{title}</p>
      <span className="mt-3 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground">
        <Upload className="h-4 w-4" /> {value ? "تغيير" : "ارفع الوثيقة"}
      </span>
      <input
        type="file"
        accept="image/*,application/pdf"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onChange(URL.createObjectURL(f), f);
        }}
      />
    </label>
  );
}
