import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import {
  BadgeCheck, Bot, FileCheck2, MessageSquareLock, ArrowLeft, ArrowRight,
  UserPlus, Camera, CheckCircle2, Star, ShieldCheck,
} from "lucide-react";
import { ListingCard } from "@/components/ListingCard";
import { MOCK_LISTINGS } from "@/lib/mock-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "معاملاتي — منصة التعاملات الموثوقة للعقارات والسيارات" },
      {
        name: "description",
        content: "معاملاتي — منصة موثوقة لبيع وتأجير العقارات والسيارات بضمان التحقق من الهوية والملكية.",
      },
      { property: "og:title", content: "معاملاتي — منصة التعاملات الموثوقة" },
      { property: "og:description", content: "ثق، تعامل، اطمئن — وسيط ذكي موثوق." },
    ],
  }),
  component: Home,
});

type Tab = "all" | "property" | "car" | "sale" | "rent";

function Home() {
  const [tab, setTab] = useState<Tab>("all");

  const filtered = MOCK_LISTINGS.filter((l) => {
    if (tab === "all") return true;
    if (tab === "property" || tab === "car") return l.category === tab;
    return l.kind === tab;
  }).slice(0, 6);

  return (
    <div>
      {/* SECTION 1 — Hero */}
      <section
        className="relative overflow-hidden py-24 text-primary-foreground"
        style={{ background: "var(--gradient-hero)" }}
      >
        {/* floating blobs */}
        <div className="pointer-events-none absolute -top-20 right-10 h-72 w-72 rounded-full bg-primary-light/30 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 left-10 h-80 w-80 rounded-full bg-accent/20 blur-3xl" />
        <div className="pointer-events-none absolute top-1/2 left-1/3 h-48 w-48 rounded-full bg-white/5 blur-2xl" />

        <div className="relative mx-auto max-w-5xl px-4 text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-1.5 text-sm backdrop-blur-md">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
            </span>
            منصة موثوقة ومرخصة
          </div>

          <h1 className="text-4xl font-extrabold leading-tight md:text-6xl">
            تعامل بثقة كاملة
            <br />
            <span className="text-accent">في كل صفقة</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base text-white/85 md:text-lg">
            مسكن — الوسيط الذكي الموثوق لبيع وتأجير العقارات  في السودان
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              to="/marketplace"
              className="rounded-md bg-accent px-7 py-3.5 font-bold text-accent-foreground shadow-lg hover:opacity-90"
            >
              🏠 تصفح المعرض
            </Link>
            <Link
              to="/register"
              className="rounded-md border-2 border-white/30 bg-white/10 px-7 py-3.5 font-bold backdrop-blur hover:bg-white/20"
            >
              ابدأ كبائع الآن
            </Link>
          </div>

          {/* Stats */}
          <div className="mx-auto mt-12 grid max-w-3xl grid-cols-3 divide-x divide-x-reverse divide-white/15 rounded-2xl border border-white/15 bg-white/5 py-5 backdrop-blur">
            {[
              { n: "+1,200", l: "إعلان موثّق" },
              { n: "+850", l: "بائع موثّق" },
              { n: "97%", l: "نسبة الرضا" },
            ].map((s) => (
              <div key={s.l} className="px-2 text-center">
                <div className="text-2xl font-extrabold md:text-3xl">{s.n}</div>
                <div className="mt-1 text-xs text-white/75 md:text-sm">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 2 — How it works */}
      <section className="mx-auto max-w-7xl px-4 py-20">
        <div className="text-center">
          <h2 className="text-3xl font-extrabold">كيف تعمل المنصة؟</h2>
          <div className="mx-auto mt-2 h-1 w-20 rounded-full bg-accent" />
          <p className="mx-auto mt-4 max-w-xl text-sm text-muted-foreground">
            أربع خطوات بسيطة تفصلك عن صفقتك الآمنة
          </p>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-4">
          {[
            { i: UserPlus, t: "سجل وأنشئ حسابك", d: "أنشئ حسابك خلال دقيقة واحدة" },
            { i: Camera, t: "ارفع السلعة وصورها", d: "صور واضحة من زوايا متعددة" },
            { i: Bot, t: "تحقق AI من الحالة", d: "تقييم آلي للحالة والوثائق" },
            { i: CheckCircle2, t: "انشر وتواصل بأمان", d: "محادثات داخل المنصة فقط" },
          ].map((s, idx, arr) => (
            <div key={s.t} className="relative">
              <div className="flex flex-col items-center rounded-2xl border bg-card p-6 text-center shadow-[var(--shadow-card)] transition hover:shadow-[var(--shadow-elevated)]">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                  {idx + 1}
                </div>
                <s.i className="h-8 w-8 text-accent" />
                <h3 className="mt-3 font-bold">{s.t}</h3>
                <p className="mt-1 text-xs text-muted-foreground">{s.d}</p>
              </div>
              {idx < arr.length - 1 && (
                <ArrowLeft className="absolute top-1/2 -left-3 hidden h-6 w-6 -translate-y-1/2 text-muted-foreground md:block" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 3 — Trust pillars */}
      <section className="bg-secondary/40">
        <div className="mx-auto max-w-7xl px-4 py-20">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold">لماذا معاملاتي؟</h2>
            <div className="mx-auto mt-2 h-1 w-20 rounded-full bg-accent" />
          </div>
          <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: BadgeCheck, title: "تحقق من الهوية", desc: "كل بائع موثّق بهويته الوطنية ومستنداته." },
              { icon: Bot, title: "تقييم بالذكاء الاصطناعي", desc: "نقيّم حالة كل سلعة قبل النشر." },
              { icon: FileCheck2, title: "وثائق ملكية أصلية", desc: "تطابق آلي بين الهوية ووثيقة الملكية." },
              { icon: MessageSquareLock, title: "تواصل داخل المنصة", desc: "يُمنع تبادل بيانات خارج المنصة لحمايتك." },
            ].map((f) => (
              <div
                key={f.title}
                className="group relative overflow-hidden rounded-2xl border bg-card p-6 shadow-[var(--shadow-card)] transition hover:-translate-y-1 hover:shadow-[var(--shadow-elevated)]"
              >
                <div
                  className="absolute inset-x-0 top-0 h-1"
                  style={{ background: "var(--gradient-brand)" }}
                />
                <f.icon className="h-10 w-10 text-primary transition group-hover:rotate-6" />
                <h3 className="mt-4 text-lg font-bold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 4 — Featured */}
      <section className="mx-auto max-w-7xl px-4 py-20">
        <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="text-3xl font-extrabold">إعلانات مميزة</h2>
            <p className="mt-1 text-sm text-muted-foreground">إعلانات موثّقة بالكامل</p>
          </div>
          <Link to="/marketplace" className="flex items-center gap-1 text-sm font-semibold text-primary hover:underline">
            عرض الكل <ArrowLeft className="h-4 w-4" />
          </Link>
        </div>

        <div className="mb-6 flex flex-wrap gap-2">
          {([
            { k: "all", l: "الكل" },
            { k: "property", l: "عقارات" },
            { k: "car", l: "سيارات" },
            { k: "sale", l: "بيع" },
            { k: "rent", l: "إيجار" },
          ] as { k: Tab; l: string }[]).map((t) => (
            <button
              key={t.k}
              onClick={() => setTab(t.k)}
              className={`rounded-full border px-4 py-1.5 text-sm font-semibold transition ${
                tab === t.k
                  ? "border-primary bg-primary text-primary-foreground"
                  : "bg-card text-foreground hover:bg-secondary"
              }`}
            >
              {t.l}
            </button>
          ))}
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((l, i) => (
            <div key={l.id} className="relative">
              {i < 2 && (
                <span className="absolute -top-2 right-3 z-10 rounded-full bg-accent px-3 py-1 text-xs font-bold text-accent-foreground shadow-md">
                  ⭐ مميز
                </span>
              )}
              <ListingCard l={l} />
            </div>
          ))}
        </div>
      </section>

      {/* SECTION 5 — Testimonials */}
      <section className="bg-secondary/40">
        <div className="mx-auto max-w-7xl px-4 py-20">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold">ماذا يقول عملاؤنا</h2>
            <div className="mx-auto mt-2 h-1 w-20 rounded-full bg-accent" />
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-3">
            {[
              {
                name: "أحمد محمد",
                city: "الخرطوم",
                quote:
                  "بعت شقتي في أسبوع واحد بعد ما اتحقق منها الموقع. ما كنت متوقع الأمر يكون سريع وآمن كده.",
              },
              {
                name: "فاطمة علي",
                city: "أم درمان",
                quote:
                  "استاجرت شقة وكنت خايفة من النصب، لكن بعد التحقق من الوثائق اطمأن قلبي تماماً.",
              },
              {
                name: "عمر حسن",
                city: "بحري",
                quote:
                  "المنصة محترفة جداً، التحقق من الهوية والملكية أعطاني ثقة كاملة في البائع.",
              },
            ].map((t) => (
              <div key={t.name} className="rounded-2xl border bg-card p-6 shadow-[var(--shadow-card)]">
                <div className="flex items-center gap-3">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary text-lg font-bold text-primary-foreground">
                    {t.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-bold">{t.name}</div>
                    <div className="text-xs text-muted-foreground">{t.city}</div>
                  </div>
                </div>
                <div className="mt-3 flex gap-0.5">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Star key={i} className="h-4 w-4 fill-accent text-accent" />
                  ))}
                </div>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">"{t.quote}"</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 6 — CTA banner */}
      <section className="mx-auto max-w-7xl px-4 py-16">
        <div
          className="relative overflow-hidden rounded-3xl px-8 py-14 text-center text-accent-foreground shadow-[var(--shadow-elevated)]"
          style={{ background: "var(--gradient-gold)" }}
        >
          <ShieldCheck className="absolute -top-6 -right-6 h-40 w-40 text-white/10" />
          <h2 className="text-3xl font-extrabold md:text-4xl">جاهز للبيع أو الشراء؟</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm md:text-base">
            انضم لآلاف المستخدمين الذين يثقون بمعاملاتي
          </p>
          <Link
            to="/register"
            className="mt-7 inline-flex items-center gap-2 rounded-md bg-primary px-7 py-3.5 font-bold text-primary-foreground hover:bg-primary-light"
          >
            ابدأ الآن مجاناً <ArrowRight className="h-4 w-4 rotate-180" />
          </Link>
        </div>
      </section>
    </div>
  );
}
