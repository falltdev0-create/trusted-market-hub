import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { UploadCloud, X, Loader2, Bot, Star } from "lucide-react";
import { toast } from "sonner";
import { StepProgress } from "@/components/StepProgress";
import { useListingStore } from "@/stores/listing";
import { uploadApi } from "@/lib/api";

export const Route = createFileRoute("/sell/upload-images")({
  head: () => ({ meta: [{ title: "رفع الصور — مسكن" }] }),
  component: UploadImages,
});

const STEPS_MSG = [
  "🔍 يتم تحليل الصور...",
  "🧠 الذكاء الاصطناعي يقيّم الحالة...",
  "📊 حساب درجة الجودة...",
  "✅ تجهيز التقرير النهائي...",
];

function UploadImages() {
  const { draft, setImages, setCondition } = useListingStore();
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>(draft.images);
  const [phase, setPhase] = useState<"idle" | "uploading" | "analyzing" | "done">("idle");
  const [progress, setProgress] = useState(0);
  const [score, setScore] = useState(0);
  const [stepIdx, setStepIdx] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const nav = useNavigate();

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  function onFiles(picked: FileList | null) {
    if (!picked) return;
    const arr = Array.from(picked);
    if (files.length + arr.length > 20) { toast.error("الحد الأقصى 20 صورة"); return; }
    const valid: File[] = [];
    for (const f of arr) {
      if (f.size > 20 * 1024 * 1024) { toast.error(`${f.name} أكبر من 20MB`); continue; }
      valid.push(f);
    }
    setFiles((p) => [...p, ...valid]);
    setPreviews((p) => [...p, ...valid.map((f) => URL.createObjectURL(f))]);
  }

  function remove(i: number) {
    setFiles((p) => p.filter((_, idx) => idx !== i));
    setPreviews((p) => p.filter((_, idx) => idx !== i));
  }

  function finishWithResult(s: number, grade: "excellent" | "good" | "poor", priceMax: number) {
    setScore(s);
    setCondition(s, grade, priceMax);
    setPhase("done");
  }

  function startPolling(listingId: string) {
    setPhase("analyzing");
    setStepIdx(0);
    let i = 0;
    const stepTimer = setInterval(() => {
      i = (i + 1) % STEPS_MSG.length;
      setStepIdx(i);
    }, 1500);

    const poll = async () => {
      try {
        const { data } = await uploadApi.getConditionResult(listingId);
        if (data?.status === "done") {
          clearInterval(stepTimer);
          if (pollRef.current) clearInterval(pollRef.current);
          const grade = (data.condition_grade ?? "good") as any;
          finishWithResult(
            Math.round((data.condition_score ?? 0.7) * 100),
            grade,
            data.price_max_limit ?? 1000000,
          );
        }
      } catch {
        // ignore transient errors
      }
    };
    pollRef.current = setInterval(poll, 3000);
    poll();

    // Safety timeout 90s — fall back to simulated result
    setTimeout(() => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        clearInterval(stepTimer);
        if (phase !== "done") {
          const s = 65 + Math.floor(Math.random() * 30);
          const grade = s >= 80 ? "excellent" : s >= 60 ? "good" : "poor";
          finishWithResult(s, grade, grade === "excellent" ? 3500000 : grade === "good" ? 1800000 : 800000);
        }
      }
    }, 90000);
  }

  async function analyze() {
    if (previews.length < 5) { toast.error("الحد الأدنى 5 صور"); return; }
    setImages(previews);

    const id = draft.id;
    if (!id || id.startsWith("local-") || files.length === 0) {
      // Offline / no backend: simulate the AI flow
      setPhase("analyzing");
      let i = 0;
      const stepTimer = setInterval(() => { i = (i + 1) % STEPS_MSG.length; setStepIdx(i); }, 1200);
      await new Promise((r) => setTimeout(r, 3500));
      clearInterval(stepTimer);
      const s = 65 + Math.floor(Math.random() * 30);
      const grade = s >= 80 ? "excellent" : s >= 60 ? "good" : "poor";
      finishWithResult(s, grade, grade === "excellent" ? 3500000 : grade === "good" ? 1800000 : 800000);
      return;
    }

    // Real upload
    try {
      setPhase("uploading");
      const fd = new FormData();
      files.forEach((f) => fd.append("images", f));
      await uploadApi.uploadImages(id, fd);
      setProgress(100);
      startPolling(id);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "فشل رفع الصور");
      setPhase("idle");
    }
  }

  if (phase === "uploading") {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-20 text-center">
        <UploadCloud className="h-16 w-16 text-primary" />
        <h2 className="mt-4 text-xl font-bold">جاري رفع الصور...</h2>
        <div className="mt-6 h-2 w-full max-w-md overflow-hidden rounded-full bg-secondary">
          <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>
    );
  }

  if (phase === "analyzing") {
    return (
      <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-20 text-center">
        <div className="relative">
          <Bot className="h-20 w-20 text-primary" />
          <Loader2 className="absolute -bottom-2 -left-2 h-8 w-8 animate-spin text-accent" />
        </div>
        <h2 className="mt-6 text-2xl font-bold">جاري تحليل الصور بالذكاء الاصطناعي... ⏳</h2>
        <p className="mt-3 text-sm text-muted-foreground">نتحقق من حالة كل صورة. قد تستغرق العملية حتى دقيقة.</p>
        <ul className="mt-8 w-full max-w-md space-y-3 text-right">
          {STEPS_MSG.map((m, i) => (
            <li
              key={m}
              className={`flex items-center gap-2 rounded-md px-3 py-2 transition ${
                i === stepIdx ? "bg-primary/10 font-semibold text-primary" : "text-muted-foreground"
              }`}
            >
              {i === stepIdx && <Loader2 className="h-3.5 w-3.5 animate-spin" />} {m}
            </li>
          ))}
        </ul>
      </div>
    );
  }

  if (phase === "done") {
    const grade = score >= 80 ? "excellent" : score >= 60 ? "good" : "poor";
    const colors = {
      excellent: "from-success/20 to-success/5 border-success/30 text-success",
      good: "from-warning/20 to-warning/5 border-warning/30 text-warning",
      poor: "from-destructive/20 to-destructive/5 border-destructive/30 text-destructive",
    }[grade];
    const labels = { excellent: "ممتازة", good: "جيدة", poor: "ضعيفة" }[grade];
    return (
      <div className="mx-auto max-w-2xl px-4 py-10">
        <StepProgress current={3} total={6} label="نتيجة تقييم الحالة" />
        <div className={`rounded-2xl border-2 bg-gradient-to-bl p-8 ${colors}`}>
          <div className="flex items-center gap-3">
            <Bot className="h-8 w-8" />
            <h2 className="text-2xl font-bold text-foreground">نتيجة الذكاء الاصطناعي</h2>
          </div>
          <div className="mt-8">
            <div className="flex items-center justify-between text-sm font-semibold text-foreground">
              <span>حالة السلعة</span>
              <span>{score}/100</span>
            </div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-card">
              <div className="h-full rounded-full bg-current transition-all duration-1000" style={{ width: `${score}%` }} />
            </div>
          </div>
          <div className="mt-6 flex items-center gap-2 text-xl font-bold">
            <Star className="h-5 w-5 fill-current" />
            <Star className="h-5 w-5 fill-current" />
            <Star className="h-5 w-5 fill-current" />
            <span className="ms-2">{labels}</span>
          </div>
          <div className="mt-6 rounded-xl bg-card p-4">
            <p className="text-sm text-muted-foreground">السعر</p>
            <p className="text-lg font-bold text-primary">لا يوجد حد إلزامي — سيظهر التصنيف السعري بعد تحديد السعر.</p>
          </div>
          <button
            onClick={() => nav({ to: "/sell/upload-docs" })}
            className="mt-8 w-full rounded-lg bg-primary py-3 font-bold text-primary-foreground hover:bg-primary-light"
          >
            متابعة ← رفع وثائق الملكية
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <StepProgress current={2} total={6} label="رفع الصور" />
      <h1 className="mb-2 text-3xl font-bold">ارفع صور العقار</h1>
      <p className="mb-6 text-muted-foreground">ارفع من 5 إلى 20 صورة — داخل وخارج العقار</p>

      <div
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); onFiles(e.dataTransfer.files); }}
        className="cursor-pointer rounded-2xl border-2 border-dashed border-primary/40 bg-primary/5 p-10 text-center transition hover:bg-primary/10"
      >
        <UploadCloud className="mx-auto h-12 w-12 text-primary" />
        <p className="mt-4 font-semibold text-foreground">اسحب الصور هنا أو انقر للاختيار</p>
        <p className="mt-1 text-sm text-muted-foreground">JPG/PNG — حتى 20MB لكل صورة</p>
        <input ref={fileRef} type="file" accept="image/*" multiple hidden onChange={(e) => onFiles(e.target.files)} />
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-muted-foreground">
          {previews.length} / 5 صور مطلوبة {previews.length >= 5 && "✅"}
        </span>
      </div>

      {previews.length > 0 && (
        <div className="mt-6 grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-5">
          {previews.map((src, i) => (
            <div key={i} className="group relative aspect-square overflow-hidden rounded-lg border">
              <img src={src} alt="" className="h-full w-full object-cover" />
              <button
                onClick={() => remove(i)}
                className="absolute left-1 top-1 rounded-full bg-destructive p-1 text-destructive-foreground opacity-0 transition group-hover:opacity-100"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="mt-8 flex justify-end">
        <button
          onClick={analyze}
          disabled={previews.length < 5}
          className="rounded-lg bg-primary px-8 py-3 font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
        >
          تحليل بالذكاء الاصطناعي
        </button>
      </div>
    </div>
  );
}
