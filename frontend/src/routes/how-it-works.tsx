import { createFileRoute, Link } from "@tanstack/react-router";
import { UserPlus, Camera, Bot, CheckCircle2, Search, MessageSquare, ShieldCheck, FileCheck2 } from "lucide-react";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import { useLanguage } from "@/i18n/LanguageContext";
import { useAuthStore } from "@/stores/auth";

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
  const { t } = useLanguage();
  const isLoggedIn = useAuthStore((state) => state.isLoggedIn);
  return (
    <div className="mx-auto max-w-5xl px-4 py-14">
      <header className="text-center">
        <h1 className="text-4xl font-extrabold">{t("howItWorks.title")}</h1>
        <p className="mx-auto mt-3 max-w-2xl text-muted-foreground">
          {t("howItWorks.intro")}
        </p>
      </header>

      <section className="mt-12">
        <h2 className="mb-6 text-2xl font-bold">{t("howItWorks.sellers")}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { i: UserPlus, t: "howItWorks.step1", d: "howItWorks.step1Description" },
            { i: Camera, t: "howItWorks.step2", d: "howItWorks.step2Description" },
            { i: Bot, t: "howItWorks.step3", d: "howItWorks.step3Description" },
            { i: FileCheck2, t: "howItWorks.step4", d: "howItWorks.step4Description" },
            { i: ShieldCheck, t: "howItWorks.step5", d: "howItWorks.step5Description" },
            { i: CheckCircle2, t: "howItWorks.step6", d: "howItWorks.step6Description" },
          ].map((s) => (
            <div key={s.t} className="rounded-xl border bg-card p-5">
              <s.i className="h-8 w-8 text-primary" />
              <h3 className="mt-3 font-bold">{t(s.t)}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t(s.d)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="mb-6 text-2xl font-bold">{t("howItWorks.buyers")}</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {[
            { i: Search, t: "howItWorks.buyerStep1", d: "howItWorks.buyerStep1Description" },
            { i: ShieldCheck, t: "howItWorks.buyerStep2", d: "howItWorks.buyerStep2Description" },
            { i: MessageSquare, t: "howItWorks.buyerStep3", d: "howItWorks.buyerStep3Description" },
            { i: CheckCircle2, t: "howItWorks.buyerStep4", d: "howItWorks.buyerStep4Description" },
          ].map((s) => (
            <div key={s.t} className="rounded-xl border bg-card p-5">
              <s.i className="h-8 w-8 text-primary" />
              <h3 className="mt-3 font-bold">{t(s.t)}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{t(s.d)}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-14">
        <h2 className="mb-6 text-2xl font-bold">{t("howItWorks.faq")}</h2>
        <Accordion type="single" collapsible className="w-full">
          {[
            { q: "howItWorks.free", a: "howItWorks.freeAnswer" },
            { q: "howItWorks.verify", a: "howItWorks.verifyAnswer" },
            { q: "howItWorks.contact", a: "howItWorks.contactAnswer" },
            { q: "howItWorks.review", a: "howItWorks.reviewAnswer" },
            { q: "howItWorks.rejected", a: "howItWorks.rejectedAnswer" },
          ].map((f, i) => (
            <AccordionItem key={i} value={`q-${i}`}>
              <AccordionTrigger className="text-right">{t(f.q)}</AccordionTrigger>
              <AccordionContent>{t(f.a)}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </section>

      {!isLoggedIn && (
        <div className="mt-14 text-center">
          <Link
            to="/register"
            className="inline-flex rounded-md bg-primary px-7 py-3.5 font-bold text-primary-foreground hover:bg-primary-light"
          >
            {t("howItWorks.start")}
          </Link>
        </div>
      )}
    </div>
  );
}
