import { Link } from "@tanstack/react-router";
import { Mail, MapPin, Phone, Facebook, Twitter, Instagram } from "lucide-react";
import { MoamalatiLogo } from "./MoamalatiLogo";
import { useLanguage } from "@/i18n/LanguageContext";

export function Footer() {
  const { t } = useLanguage();
  return (
    <footer className="mt-16 border-t-2 border-t-accent bg-card">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 md:grid-cols-6">
        <div className="md:col-span-2">
          <MoamalatiLogo showTagline />
          <p className="mt-3 max-w-md text-sm text-muted-foreground">
            {t("footer.description")}
          </p>
          <div className="mt-4 flex gap-2">
            {[Facebook, Twitter, Instagram].map((Ic, i) => (
              <a
                key={i}
                href="#"
                className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary text-muted-foreground hover:bg-primary hover:text-primary-foreground"
                aria-label={t("footer.social")}
              >
                <Ic className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        <FooterCol
          title={t("footer.quickLinks")}
          items={[
            { label: t("navigation.marketplace"), to: "/marketplace" },
            { label: t("navigation.howItWorks"), to: "/how-it-works" },
            { label: t("navigation.about"), to: "/" },
          ]}
        />
        <FooterCol
          title={t("footer.sellers")}
          items={[
            { label: t("footer.createListing"), to: "/sell/new" },
            { label: t("navigation.myListings"), to: "/my-listings" },
            { label: t("footer.sellingGuide"), to: "/how-it-works" },
          ]}
        />
        <FooterCol
          title={t("footer.buyers")}
          items={[
            { label: t("footer.browseProperties"), to: "/marketplace" },
      
            { label: t("footer.howToBuy"), to: "/how-it-works" },
          ]}
        />

        <div>
          <h4 className="mb-3 font-semibold text-foreground">{t("footer.contact")}</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2"><MapPin className="mt-0.5 h-4 w-4 shrink-0" /><span>{t("footer.location")}</span></li>
            <li className="flex items-center gap-2"><Mail className="h-4 w-4" /><span>info@moamalati.sd</span></li>
            <li className="flex items-center gap-2"><Phone className="h-4 w-4" /><span>+249 900 000 000</span></li>
          </ul>
        </div>
      </div>
      <div className="border-t py-4 text-center text-xs text-muted-foreground">
        {t("footer.copyright", { year: new Date().getFullYear() })}
      </div>
    </footer>
  );
}

function FooterCol({ title, items }: { title: string; items: { label: string; to: string }[] }) {
  return (
    <div>
      <h4 className="mb-3 font-semibold text-foreground">{title}</h4>
      <ul className="space-y-2 text-sm text-muted-foreground">
        {items.map((it) => (
          <li key={it.label}>
            <Link to={it.to} className="hover:text-primary">{it.label}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
