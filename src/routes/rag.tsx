import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Loader2, Search, Sparkles, Database, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { ragApi } from "@/lib/api";

export const Route = createFileRoute("/rag")({
  head: () => ({
    meta: [
      { title: "مختبر RAG — معاملاتي" },
      { name: "description", content: "اختبر البحث الدلالي والإجابة الذكية المبنية على نماذج الذكاء الاصطناعي المحلية في منصة معاملاتي." },
      { property: "og:title", content: "مختبر RAG — معاملاتي" },
      { property: "og:description", content: "بحث دلالي وإجابات ذكية مع المصادر من فهرس إعلانات معاملاتي." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: RagLab,
});

function RagLab() {
  const [status, setStatus] = useState<any>(null);
  const [q, setQ] = useState("شقة للإيجار في الخرطوم");
  const [busy, setBusy] = useState<"" | "search" | "ask" | "index">("");
  const [results, setResults] = useState<any[]>([]);
  const [answer, setAnswer] = useState<string>("");

  const loadStatus = () =>
    ragApi
      .status()
      .then((r: any) => setStatus(r.data))
      .catch(() => setStatus({ ok: false }));

  useEffect(() => {
    loadStatus();
  }, []);

  async function run(mode: "search" | "ask") {
    if (!q.trim()) return;
    setBusy(mode);
    setAnswer("");
    try {
      if (mode === "search") {
        const r: any = await ragApi.search(q, 5);
        setResults(r.data?.results ?? []);
      } else {
        const r: any = await ragApi.ask(q, 5);
        setAnswer(r.data?.answer ?? "");
        setResults(r.data?.sources ?? []);
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "تعذّر الاتصال بخدمة RAG");
    } finally {
      setBusy("");
    }
  }

  async function indexListings() {
    setBusy("index");
    try {
      const r: any = await ragApi.indexListings();
      toast.success(`تمت فهرسة ${r.data?.indexed_listings ?? 0} إعلاناً`);
      loadStatus();
    } catch (e: any) {
      toast.error(e?.response?.data?.detail ?? "الفهرسة تتطلب صلاحية مشرف");
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="mb-2 text-3xl font-bold">مختبر RAG</h1>
      <p className="mb-6 text-muted-foreground">
        بحث دلالي وإجابات ذكية عبر نماذج Hugging Face المحلية المرتبطة بالباكند.
      </p>

      <div className="mb-6 rounded-2xl border bg-card p-5">
        <div className="mb-3 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold">
            <Database className="h-4 w-4 text-primary" /> حالة الفهرس
          </div>
          <button onClick={loadStatus} className="rounded-lg border px-2 py-1 text-xs font-semibold hover:bg-secondary">
            <RefreshCw className="inline h-3.5 w-3.5" /> تحديث
          </button>
        </div>
        {status == null ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <div className="grid gap-2 text-sm sm:grid-cols-2">
            <div>المستندات: <b>{status.documents ?? 0}</b></div>
            <div>نموذج التضمين: <b className="break-all">{status.embedding_model ?? "—"}</b></div>
            <div>نموذج التوليد: <b className="break-all">{status.llm_model ?? "—"}</b></div>
            <div>
              الوضع:{" "}
              <b className={status.embedding_fallback ? "text-warning" : "text-success"}>
                {status.embedding_fallback ? "بديل hashing (النموذج غير محمّل)" : "نموذج محلي محمّل"}
              </b>
            </div>
          </div>
        )}
        <button
          onClick={indexListings}
          disabled={busy === "index"}
          className="mt-4 rounded-lg bg-primary px-3 py-2 text-sm font-bold text-primary-foreground disabled:opacity-60"
        >
          {busy === "index" ? <Loader2 className="inline h-4 w-4 animate-spin" /> : "فهرسة الإعلانات المنشورة"}
        </button>
      </div>

      <div className="rounded-2xl border bg-card p-5">
        <textarea
          value={q}
          onChange={(e) => setQ(e.target.value)}
          rows={3}
          className="w-full rounded-xl border bg-background p-3 text-sm outline-none focus:border-primary"
          placeholder="اكتب سؤالك أو استعلامك…"
        />
        <div className="mt-3 flex gap-2">
          <button
            onClick={() => run("search")}
            disabled={!!busy}
            className="rounded-lg border px-4 py-2 text-sm font-bold hover:bg-secondary disabled:opacity-60"
          >
            {busy === "search" ? <Loader2 className="inline h-4 w-4 animate-spin" /> : <Search className="inline h-4 w-4" />} بحث دلالي
          </button>
          <button
            onClick={() => run("ask")}
            disabled={!!busy}
            className="rounded-lg bg-accent px-4 py-2 text-sm font-bold text-accent-foreground disabled:opacity-60"
          >
            {busy === "ask" ? <Loader2 className="inline h-4 w-4 animate-spin" /> : <Sparkles className="inline h-4 w-4" />} اسأل الذكاء الاصطناعي
          </button>
        </div>

        {answer && (
          <div className="mt-4 rounded-xl bg-primary/5 p-4 text-sm leading-7">{answer}</div>
        )}

        {results.length > 0 && (
          <ul className="mt-4 space-y-2">
            {results.map((r: any) => (
              <li key={r.id} className="rounded-xl border p-3 text-sm">
                <div className="flex justify-between gap-3">
                  <b>{r.title || r.source}</b>
                  <span className="shrink-0 text-xs text-muted-foreground">{r.score}</span>
                </div>
                {r.content && <p className="mt-1 text-muted-foreground line-clamp-3">{r.content}</p>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
