import { createFileRoute, Link } from "@tanstack/react-router";
import { UserPlus, Camera, Bot, CheckCircle2, Search, MessageSquare, ShieldCheck, FileCheck2 } from "lucide-react";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";

export const Route = createFileRoute("/how-it-works")({
  head: () => ({
    meta: [
      { title: "كيف يعمل — مسكن" },
      { name: "description", content: "تعرف على خطوات البيع والشراء عبر مسكن بضمان وأمان كامل." },
    ],
  }),
  component: HowItWorks,
});

function HowItWorks() {
  return (
    <div className="mx-auto max-w-5xl px-4 py-14">
      <header className="text-center">
        <h1 className="text-4xl font-extrabold">كيف يعمل مسكن</h1>
        <p className="mx-auto mt-3 max-w-2xl text-muted-foreground">
          منصة وسيطة موثوقة — نتحقق من كل بائع، كل وثيقة، وكل صفقة.
        </p>
      </header>

      <section className="mt-12">
        <h2 className="mb-6 text-2xl font-bold">للبائعين</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { i: UserPlus, t: "1. سجل وأنشئ حسابك", d: "بريد إلكتروني ورقم هاتف فقط." },
            { i: Camera, t: "2. ارفع صور السلعة", d: "صور عالية الجودة من زوايا متعددة." },
            { i: Bot, t: "3. تقييم AI تلقائي", d: "تحليل ذكي لحالة السلعة." },
            { i: FileCheck2, t: "4. تحقق من الوثائق", d: "ارفع هويتك وعقد الملكية." },
            { i: ShieldCheck, t: "5. مراجعة الإدارة", d: "تحقق نهائي قبل النشر." },
            { i: CheckCircle2, t: "6. النشر والتواصل", d: "استقبل المشترين بثقة." },
          ].map((s) => (
            <div key={s.t} className="rounded-xl border bg-card p-5">
              <s.i className="h-8 w-8 text-primary" />
              <h3 className="mt-3 font-bold">{s.t}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="mb-6 text-2xl font-bold">للمشترين</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { i: Search, t: "1. تصفح المعرض", d: "آلاف الإعلانات الموثقة." },
            { i: ShieldCheck, t: "2. تحقق من الموثوقية", d: "كل إعلان مدقق بالكامل." },
            { i: MessageSquare, t: "3. تواصل عبر المنصة", d: "محادثة آمنة مع البائع." },
            { i: CheckCircle2, t: "4. أتمم الصفقة بأمان", d: "بضمان مسكن." },
          ].map((s) => (
            <div key={s.t} className="rounded-xl border bg-card p-5">
              <s.i className="h-8 w-8 text-primary" />
              <h3 className="mt-3 font-bold">{s.t}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{s.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="mb-6 text-2xl font-bold">الأسئلة الشائعة</h2>
        <Accordion type="single" collapsible className="w-full">
          {[
            { q: "هل المنصة مجانية؟", a: "نعم، التسجيل والتصفح مجانيان بالكامل." },
            { q: "كيف يتم التحقق من البائعين؟", a: "نتحقق من الهوية الوطنية ووثيقة الملكية بالذكاء الاصطناعي." },
            { q: "هل يمكنني تبادل أرقام التواصل؟", a: "لا، التواصل يتم داخل المنصة فقط لحمايتك." },
            { q: "كم تستغرق مراجعة الإعلان؟", a: "عادةً أقل من 24 ساعة." },
            { q: "ماذا لو رُفض إعلاني؟", a: "يمكنك معالجة السبب وإعادة الإرسال." },
          ].map((f, i) => (
            <AccordionItem key={i} value={`q-${i}`}>
              <AccordionTrigger className="text-right">{f.q}</AccordionTrigger>
              <AccordionContent>{f.a}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      <div className="mt-14 text-center">
        <Link
          to="/register"
          className="inline-flex rounded-md bg-primary px-7 py-3.5 font-bold text-primary-foreground hover:bg-primary-light"
        >
          ابدأ الآن
        </Link>
      </div>
    </div>
  );
}
