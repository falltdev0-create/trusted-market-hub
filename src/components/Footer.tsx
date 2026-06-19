import { Link } from "@tanstack/react-router";
import { Mail, MapPin, Phone, Facebook, Twitter, Instagram } from "lucide-react";
import { MoamalatiLogo } from "./MoamalatiLogo";

export function Footer() {
  return (
    <footer className="mt-16 border-t-2 border-t-accent bg-card">
      <div className="mx-auto grid max-w-7xl gap-8 px-4 py-12 md:grid-cols-6">
        <div className="md:col-span-2">
          <MoamalatiLogo showTagline />
          <p className="mt-3 max-w-md text-sm text-muted-foreground">
            منصة سودانية موثوقة للوساطة في بيع وتأجير العقارات . نتحقق من الهوية والملكية لضمان أمان الصفقات.
          </p>
          <div className="mt-4 flex gap-2">
            {[Facebook, Twitter, Instagram].map((Ic, i) => (
              <a
                key={i}
                href="#"
                className="flex h-9 w-9 items-center justify-center rounded-full bg-secondary text-muted-foreground hover:bg-primary hover:text-primary-foreground"
                aria-label="social"
              >
                <Ic className="h-4 w-4" />
              </a>
            ))}
          </div>
        </div>

        <FooterCol
          title="روابط سريعة"
          items={[
            { label: "المعرض", to: "/marketplace" },
            { label: "كيف يعمل", to: "/how-it-works" },
            { label: "عن المنصة", to: "/" },
          ]}
        />
        <FooterCol
          title="للبائعين"
          items={[
            { label: "إنشاء إعلان", to: "/sell/new" },
            { label: "إعلاناتي", to: "/my-listings" },
            { label: "دليل البيع", to: "/how-it-works" },
          ]}
        />
        <FooterCol
          title="للمشترين"
          items={[
            { label: "تصفح العقارات", to: "/marketplace" },
      
            { label: "كيف أشتري؟", to: "/how-it-works" },
          ]}
        />

        <div>
          <h4 className="mb-3 font-semibold text-foreground">تواصل معنا</h4>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2"><MapPin className="mt-0.5 h-4 w-4 shrink-0" /><span>الخرطوم، السودان</span></li>
            <li className="flex items-center gap-2"><Mail className="h-4 w-4" /><span>info@moamalati.sd</span></li>
            <li className="flex items-center gap-2"><Phone className="h-4 w-4" /><span>+249 900 000 000</span></li>
          </ul>
        </div>
      </div>
      <div className="border-t py-4 text-center text-xs text-muted-foreground">
        © {new Date().getFullYear()} مسكن — جميع الحقوق محفوظة · سياسة الخصوصية · الشروط والأحكام
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
