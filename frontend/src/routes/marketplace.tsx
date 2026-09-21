import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { Search, SlidersHorizontal } from "lucide-react";
import { ListingCard } from "@/components/ListingCard";
import { MOCK_LISTINGS, CITIES } from "@/lib/mock-data";
import { useLanguage } from "@/i18n/LanguageContext";
import { getCityName } from "@/i18n/cities";

export const Route = createFileRoute("/marketplace")({
  head: () => ({
    meta: [
      { title: "المعرض — مسكن" },
      {
        name: "description",
        content: "تصفح إعلانات العقارات الموثوقة في مسكن.",
      },
    ],
  }),
  component: Marketplace,
});

type Tab = "all" | "property" ;
type Sort = "newest" | "price_asc" | "price_desc";

function Marketplace() {
  const { t } = useLanguage();
  const [tab, setTab] = useState<Tab>("all");
  const [sort, setSort] = useState<Sort>("newest");
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<"all" | "sale" | "rent">("all");
  const [grades, setGrades] = useState<string[]>([]);
  const [city, setCity] = useState<string[]>([]);
  const [price, setPrice] = useState<[number, number]>([0, 5000000]);

  const filtered = useMemo(() => {
    let arr = [...MOCK_LISTINGS];
    if (tab !== "all") arr = arr.filter((l) => l.category === tab);
    if (kind !== "all") arr = arr.filter((l) => l.kind === kind);
    if (grades.length) arr = arr.filter((l) => grades.includes(l.grade));
    if (city.length) arr = arr.filter((l) => city.includes(l.city));
    if (query) arr = arr.filter((l) => l.title.includes(query));
    arr = arr.filter((l) => l.price >= price[0] && l.price <= price[1]);
    if (sort === "price_asc") arr.sort((a, b) => a.price - b.price);
    if (sort === "price_desc") arr.sort((a, b) => b.price - a.price);
    return arr;
  }, [tab, kind, grades, city, query, price, sort]);

  function toggle<T>(list: T[], v: T, set: (l: T[]) => void) {
    set(list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="mb-6 text-3xl font-bold">{t("marketplace.title")}</h1>

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Sidebar */}
        <aside className="sticky top-20 h-fit rounded-2xl border bg-card p-5">
          <div className="mb-4 flex items-center gap-2 font-bold">
            <SlidersHorizontal className="h-4 w-4" /> {t("marketplace.filters")}
          </div>

          <div className="space-y-5">
            <div>
              <h4 className="mb-2 text-sm font-semibold">{t("marketplace.listingType")}</h4>
              <div className="flex gap-2">
                {[
                  { v: "all", l: t("common.all") },
                  { v: "sale", l: t("common.sale") },
                  { v: "rent", l: t("common.rent") },
                ].map((o) => (
                  <button
                    key={o.v}
                    onClick={() => setKind(o.v as any)}
                    className={`flex-1 rounded-md border px-3 py-1.5 text-xs font-semibold ${
                      kind === o.v
                        ? "border-primary bg-primary text-primary-foreground"
                        : "hover:bg-secondary"
                    }`}
                  >
                    {o.l}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-sm font-semibold">{t("marketplace.condition")}</h4>
              <div className="space-y-1.5">
                {[
                  { v: "excellent", l: t("common.firstGrade"), c: "bg-success" },
                  { v: "good", l: t("common.secondGrade"), c: "bg-warning" },
                  { v: "poor", l: t("common.thirdGrade"), c: "bg-destructive" },
                ].map((o) => (
                  <label key={o.v} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={grades.includes(o.v)}
                      onChange={() => toggle(grades, o.v, setGrades)}
                    />
                    <span className={`h-2.5 w-2.5 rounded-full ${o.c}`} /> {o.l}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-sm font-semibold">{t("marketplace.city")}</h4>
              <div className="max-h-40 space-y-1.5 overflow-y-auto">
                {CITIES.map((c) => (
                  <label key={c} className="flex cursor-pointer items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={city.includes(c)}
                      onChange={() => toggle(city, c, setCity)}
                    />
                    {getCityName(c, t)}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <h4 className="mb-2 text-sm font-semibold">{t("marketplace.priceRange")}</h4>
              <div className="flex items-center gap-2 text-xs">
                <input
                  type="number"
                  value={price[0]}
                  onChange={(e) => setPrice([+e.target.value, price[1]])}
                  className="w-full rounded border bg-card px-2 py-1.5"
                />
                <span>—</span>
                <input
                  type="number"
                  value={price[1]}
                  onChange={(e) => setPrice([price[0], +e.target.value])}
                  className="w-full rounded border bg-card px-2 py-1.5"
                />
              </div>
            </div>
          </div>
        </aside>

        {/* Main */}
        <div>
          <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute end-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                placeholder={t("marketplace.searchPlaceholder")}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full rounded-lg border bg-card px-4 py-2.5 pe-10 outline-none focus:border-primary"
              />
            </div>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as Sort)}
              className="rounded-lg border bg-card px-3 py-2.5 text-sm font-semibold"
            >
              <option value="newest">{t("marketplace.newest")}</option>
              <option value="price_asc">{t("marketplace.priceAscending")}</option>
              <option value="price_desc">{t("marketplace.priceDescending")}</option>
            </select>
          </div>

          <div className="mb-5 flex gap-2 border-b">
            {[
              { v: "all", l: t("common.all") },
              { v: "property", l: t("common.property") },
              
            ].map((t) => (
              <button
                key={t.v}
                onClick={() => setTab(t.v as Tab)}
                className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition ${
                  tab === t.v
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
              >
                {t.l}
              </button>
            ))}
          </div>

          {filtered.length === 0 ? (
            <div className="rounded-xl border bg-card p-12 text-center text-muted-foreground">
              {t("listing.noMatches")}
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((l) => (
                <ListingCard key={l.id} l={l} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
