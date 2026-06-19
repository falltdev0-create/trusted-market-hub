import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect, useCallback } from "react";
import {
  MapPin,
  Star,
  ShieldCheck,
  MessageCircle,
  Bot,
  BadgeCheck,
  AlertTriangle,
  Calendar,
  Share2,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { toast } from "sonner";
import { MOCK_LISTINGS } from "@/lib/mock-data";
import { useAuthStore } from "@/stores/auth";

export const Route = createFileRoute("/listing/$id")({
  head: ({ params }) => {
    const l = MOCK_LISTINGS.find((x) => x.id === params.id);
    return {
      meta: [
        { title: l ? `${l.title} — معاملاتي` : "إعلان — معاملاتي" },
        { name: "description", content: l?.title ?? "إعلان موثّق" },
        { property: "og:image", content: l?.image ?? "" },
      ],
    };
  },
  component: ListingDetail,
});

function ListingDetail() {
  const { id } = Route.useParams();
  const l = MOCK_LISTINGS.find((x) => x.id === id);
  const [activeImg, setActiveImg] = useState(0);
  const [modalOpen, setModalOpen] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const { isLoggedIn } = useAuthStore();
  const nav = useNavigate();

  const imgs = l ? [l.image, l.image, l.image, l.image] : [];

  // Keyboard navigation for gallery (RTL: ArrowRight = previous)
  const prev = useCallback(() => setActiveImg((i) => (i - 1 + imgs.length) % imgs.length), [imgs.length]);
  const next = useCallback(() => setActiveImg((i) => (i + 1) % imgs.length), [imgs.length]);
  useEffect(() => {
    if (!imgs.length) return;
    const onKey = (e: KeyboardEvent) => {
      if (modalOpen) return;
      if (e.key === "ArrowRight") prev();
      else if (e.key === "ArrowLeft") next();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [prev, next, imgs.length, modalOpen]);

  async function share() {
    if (!l) return;
    const data = { title: l.title, text: l.title, url: typeof window !== "undefined" ? window.location.href : "" };
    try {
      if (typeof navigator !== "undefined" && (navigator as any).share) {
        await (navigator as any).share(data);
      } else {
        await navigator.clipboard.writeText(data.url);
        toast.success("تم نسخ رابط الإعلان");
      }
    } catch {
      /* user cancelled */
    }
  }

  if (!l) return <div className="p-10 text-center">الإعلان غير موجود</div>;

  function confirmChat() {
    if (!isLoggedIn) {
      nav({ to: "/login" });
      return;
    }
    setModalOpen(false);
    nav({ to: "/chat/$conversationId", params: { conversationId: l!.id } });
  }


  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="grid gap-8 lg:grid-cols-[1fr_360px]">
        <div>
          {/* Gallery */}
          <div className="overflow-hidden rounded-2xl border bg-card">
            <div className="relative aspect-video group">
              <img src={imgs[activeImg]} alt={l.title} className="h-full w-full object-cover" />
              <button
                onClick={prev}
                aria-label="السابق"
                className="absolute end-3 top-1/2 -translate-y-1/2 rounded-full bg-black/45 p-2 text-white opacity-0 transition group-hover:opacity-100 hover:bg-black/70"
              >
                <ChevronRight className="h-5 w-5" />
              </button>
              <button
                onClick={next}
                aria-label="التالي"
                className="absolute start-3 top-1/2 -translate-y-1/2 rounded-full bg-black/45 p-2 text-white opacity-0 transition group-hover:opacity-100 hover:bg-black/70"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <button
                onClick={share}
                aria-label="مشاركة"
                className="absolute start-3 top-3 rounded-full bg-black/45 p-2 text-white hover:bg-black/70"
              >
                <Share2 className="h-4 w-4" />
              </button>
              <span className="absolute end-3 top-3 rounded-md bg-black/55 px-2 py-1 text-xs font-semibold text-white">
                {activeImg + 1} / {imgs.length}
              </span>
            </div>
            <div className="grid grid-cols-4 gap-2 p-2">
              {imgs.map((src, i) => (
                <button
                  key={i}
                  onClick={() => setActiveImg(i)}
                  aria-label={`صورة ${i + 1}`}
                  className={`aspect-video overflow-hidden rounded transition ${
                    activeImg === i ? "ring-2 ring-primary" : "opacity-70 hover:opacity-100"
                  }`}
                >
                  <img src={src} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          </div>


          {/* Info */}
          <div className="mt-6 rounded-2xl border bg-card p-6">
            <div className="flex items-start justify-between gap-3">
              <h1 className="text-2xl font-bold">{l.title}</h1>
              <span className="flex items-center gap-1 rounded-md bg-success/10 px-2.5 py-1 text-xs font-bold text-success">
                <Star className="h-3 w-3 fill-current" /> ممتازة
              </span>
            </div>
            <p className="mt-2 flex items-center gap-1 text-muted-foreground">
              <MapPin className="h-4 w-4" /> {l.city}، {l.area}
            </p>

            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              {l.category === "property" ? (
                <>
                  <Spec label="غرف" value={l.bedrooms} />
                  <Spec label="حمامات" value={l.bathrooms} />
                  <Spec label="المساحة" value={`${l.size}م²`} />
                </>
              ) : (
                <>
                  <Spec label="سنة الصنع" value={l.year} />
                  <Spec label="المسافة" value={`${l.km?.toLocaleString()} كم`} />
                  <Spec label="الحالة" value="ممتازة" />
                </>
              )}
            </div>

            <div className="mt-6 border-t pt-6">
              <h3 className="mb-3 font-bold">الوصف</h3>
              <p className="text-muted-foreground">
                {l.title} — موقع مميز وحالة ممتازة. تواصل مع البائع لمزيد من التفاصيل والمعاينة.
              </p>
            </div>

            {/* AI report */}
            <details className="mt-6 rounded-xl border bg-primary/5 p-4" open>
              <summary className="flex cursor-pointer items-center gap-2 font-bold">
                <Bot className="h-5 w-5 text-primary" /> تقرير الذكاء الاصطناعي
              </summary>
              <div className="mt-4 space-y-2 text-sm">
                {[
                  ["الحالة العامة", 92],
                  ["جودة الصور", 85],
                  ["النظافة", 88],
                  ["الصيانة", 80],
                ].map(([label, val]) => (
                  <div key={label as string}>
                    <div className="flex justify-between text-muted-foreground">
                      <span>{label}</span>
                      <span className="font-semibold text-foreground">{val}/100</span>
                    </div>
                    <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-card">
                      <div className="h-full bg-success" style={{ width: `${val}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </details>

            <div className="mt-6 aspect-video rounded-xl bg-secondary p-4 text-center text-sm text-muted-foreground">
              <MapPin className="mx-auto mt-12 h-10 w-10 opacity-40" />
              خريطة الموقع (تجريبية)
            </div>
          </div>
        </div>

        {/* Sticky sidebar */}
        <aside className="sticky top-20 h-fit space-y-4">
          <div className="rounded-2xl border bg-card p-6 shadow-[var(--shadow-card)]">
            <div className="text-3xl font-extrabold text-primary">
              {l.price.toLocaleString()}{" "}
              <span className="text-base font-normal">جنيه</span>
            </div>

            <ul className="mt-5 space-y-2 text-sm">
              <li className="flex items-center gap-2">
                <Star className="h-4 w-4 fill-warning text-warning" /> حالة ممتازة (87/100)
              </li>
              <li className="flex items-center gap-2">
                <BadgeCheck className="h-4 w-4 text-success" /> هوية موثّقة
              </li>
              <li className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-success" /> ملكية موثّقة
              </li>
            </ul>

            <button
              onClick={() => setModalOpen(true)}
              className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3 font-bold text-primary-foreground hover:bg-primary-light"
            >
              <MessageCircle className="h-5 w-5" /> تواصل مع البائع
            </button>
          </div>

          <div className="rounded-2xl border bg-card p-5">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-lg font-bold text-primary">
                م
              </div>
              <div>
                <div className="flex items-center gap-1 font-bold">
                  محمد أحمد <BadgeCheck className="h-4 w-4 text-success" />
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Calendar className="h-3 w-3" /> عضو منذ 2023
                </div>
              </div>
            </div>
          </div>
        </aside>
      </div>

      {/* Mobile sticky bottom CTA */}
      <div className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-between gap-3 border-t bg-card/95 p-3 shadow-[0_-4px_16px_rgba(0,0,0,0.06)] backdrop-blur lg:hidden">
        <div>
          <div className="text-lg font-extrabold text-primary">
            {l.price.toLocaleString()} <span className="text-xs font-normal">جنيه</span>
          </div>
          <div className="text-[11px] text-muted-foreground">تحت مظلة معاملاتي</div>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-bold text-primary-foreground hover:bg-primary-light"
        >
          <MessageCircle className="h-4 w-4" /> تواصل مع البائع
        </button>
      </div>
      <div className="h-20 lg:hidden" aria-hidden="true" />


      {/* Disclaimer modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-card p-6 shadow-2xl">
            <div className="flex items-center gap-2 text-warning">
              <AlertTriangle className="h-6 w-6" />
              <h2 className="text-xl font-bold">إقرار هام</h2>
            </div>
            <div className="mt-4 space-y-3 text-sm text-foreground">
              <p>بموجب هذا الإقرار، أنت توافق على أن:</p>
              <ol className="list-decimal space-y-2 pe-5">
                <li>منصة معاملاتي تتحقق من هوية البائع وملكيته للسلعة فقط.</li>
                <li>
                  المنصة غير مسؤولة عن أي خسارة ناتجة عن الدفع قبل معاينة السلعة ميدانياً والتأكد
                  منها.
                </li>
                <li>يُمنع تبادل بيانات التواصل الشخصية خارج المنصة.</li>
              </ol>
            </div>
            <label className="mt-5 flex items-start gap-2 rounded-lg bg-secondary p-3 text-sm">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="mt-1"
              />
              <span>أوافق على الإقرار وأتحمل المسؤولية الكاملة</span>
            </label>
            <div className="mt-5 flex justify-end gap-2">
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-md px-4 py-2 text-sm font-semibold hover:bg-secondary"
              >
                إلغاء
              </button>
              <button
                disabled={!agreed}
                onClick={confirmChat}
                className="rounded-md bg-primary px-5 py-2 text-sm font-bold text-primary-foreground hover:bg-primary-light disabled:opacity-50"
              >
                موافق وتواصل
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Spec({ label, value }: { label: string; value: any }) {
  return (
    <div className="rounded-lg bg-secondary p-3 text-center">
      <div className="text-lg font-bold">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
