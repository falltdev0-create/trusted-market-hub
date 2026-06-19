import { Link } from "@tanstack/react-router";
import { BedDouble, Bath, Ruler, MapPin, ShieldCheck, Star } from "lucide-react";

export interface Listing {
  id: string;
  title: string;
  city: string;
  area: string;
  price: number;
  kind: "sale" | "rent";
  category: "property" ;
  grade: "excellent" | "good" | "poor";
  image: string;
  bedrooms?: number;
  bathrooms?: number;
  size?: number;
  year?: number;
  km?: number;
}

const gradeMap = {
  excellent: { label: "درجة أولى", color: "bg-success/10 text-success" },
  good: { label: "درجة ثانية", color: "bg-warning/10 text-warning" },
  poor: { label: "درجة ثالثة", color: "bg-destructive/10 text-destructive" },
};

export function ListingCard({ l }: { l: Listing }) {
  const g = gradeMap[l.grade];
  return (
    <Link
      to="/listing/$id"
      params={{ id: l.id }}
      className="group block overflow-hidden rounded-xl border bg-card transition-all hover:-translate-y-1 hover:shadow-[var(--shadow-elevated)]"
    >
      <div className="relative aspect-video overflow-hidden bg-secondary">
        <img
          src={l.image}
          alt={l.title}
          className="h-full w-full object-cover transition-transform group-hover:scale-105"
        />
        <div className="absolute right-3 top-3 rounded-md bg-primary px-2.5 py-1 text-xs font-bold text-primary-foreground">
          {l.kind === "sale" ? "بيع" : "إيجار"}
        </div>
        <div
          className={`absolute left-3 top-3 flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-bold ${g.color}`}
        >
          <Star className="h-3 w-3 fill-current" /> {g.label}
        </div>
      </div>
      <div className="p-4">
        <h3 className="line-clamp-1 font-bold text-foreground">{l.title}</h3>
        <p className="mt-1 flex items-center gap-1 text-sm text-muted-foreground">
          <MapPin className="h-3.5 w-3.5" /> {l.city}، {l.area}
        </p>
        {l.category === "property" ? (
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <BedDouble className="h-3.5 w-3.5" /> {l.bedrooms} غرف
            </span>
            <span className="flex items-center gap-1">
              <Bath className="h-3.5 w-3.5" /> {l.bathrooms} حمام
            </span>
            <span className="flex items-center gap-1">
              <Ruler className="h-3.5 w-3.5" /> {l.size}م²
            </span>
          </div>
        ) : (
          <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground">
            <span>{l.year}</span>
            <span>{l.km?.toLocaleString()} كم</span>
          </div>
        )}
        <div className="mt-4 flex items-center justify-between border-t pt-3">
          <span className="text-lg font-bold text-primary">
            {l.price.toLocaleString()} <span className="text-xs font-normal">جنيه</span>
          </span>
          <span className="flex items-center gap-1 text-xs font-semibold text-success">
            <ShieldCheck className="h-3.5 w-3.5" /> موثّق
          </span>
        </div>
      </div>
    </Link>
  );
}
