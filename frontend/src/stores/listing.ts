import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ListingKind = "sale_property" | "rent_property" | "sale_car" | "rent_car";

export function kindToParts(kind: ListingKind): { category: "property" | "car"; listing_type: "sale" | "rent" } {
  const [t, c] = kind.split("_");
  return { category: c as any, listing_type: t as any };
}

export interface ListingDraft {
  id?: string;
  kind?: ListingKind;
  images: string[];
  conditionScore?: number;
  conditionGrade?: "excellent" | "good" | "poor";
  priceMax?: number;
  idDocUploaded?: boolean;
  ownershipDocUploaded?: boolean;
  verified?: boolean;
  details?: Record<string, any>;
  price?: number;
  step: number;
}

interface ListingState {
  draft: ListingDraft;
  setId: (id: string) => void;
  setKind: (k: ListingKind) => void;
  setImages: (imgs: string[]) => void;
  setCondition: (score: number, grade: ListingDraft["conditionGrade"], priceMax: number) => void;
  setDocs: (id: boolean, own: boolean, verified: boolean) => void;
  setDetails: (d: Record<string, any>) => void;
  setPrice: (p: number) => void;
  setStep: (s: number) => void;
  reset: () => void;
}

const initial: ListingDraft = { images: [], step: 1 };

export const useListingStore = create<ListingState>()(
  persist(
    (set) => ({
      draft: initial,
      setId: (id) => set((s) => ({ draft: { ...s.draft, id } })),
      setKind: (kind) => set((s) => ({ draft: { ...s.draft, kind, step: 2 } })),
      setImages: (images) => set((s) => ({ draft: { ...s.draft, images } })),
      setCondition: (conditionScore, conditionGrade, priceMax) =>
        set((s) => ({ draft: { ...s.draft, conditionScore, conditionGrade, priceMax, step: 4 } })),
      setDocs: (idDocUploaded, ownershipDocUploaded, verified) =>
        set((s) => ({
          draft: { ...s.draft, idDocUploaded, ownershipDocUploaded, verified, step: 5 },
        })),
      setDetails: (details) => set((s) => ({ draft: { ...s.draft, details, step: 6 } })),
      setPrice: (price) => set((s) => ({ draft: { ...s.draft, price } })),
      setStep: (step) => set((s) => ({ draft: { ...s.draft, step } })),
      reset: () => set({ draft: initial }),
    }),
    { name: "tm_listing_draft" },
  ),
);
