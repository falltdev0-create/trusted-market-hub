import type { Listing } from "@/components/ListingCard";

export const MOCK_LISTINGS: Listing[] = [
  {
    id: "1",
    title: "شقة فاخرة في الخرطوم 2",
    city: "الخرطوم",
    area: "المنشية",
    price: 850000,
    kind: "sale",
    category: "property",
    grade: "excellent",
    image: "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800",
    bedrooms: 4,
    bathrooms: 2,
    size: 180
  },
  {
    id: "2",
    title: "فيلا حديثة في كافوري",
    city: "بحري",
    area: "كافوري",
    price: 2400000,
    kind: "sale",
    category: "property",
    grade: "excellent",
    image: "https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800",
    bedrooms: 6,
    bathrooms: 4,
    size: 450
  },
  {
    id: "4",
    title: "شقة للإيجار في أم درمان",
    city: "أم درمان",
    area: "العرب",
    price: 8500,
    kind: "rent",
    category: "property",
    grade: "good",
    image: "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800",
    bedrooms: 3,
    bathrooms: 2,
    size: 120
  },
  {
    id: "7",
    title: "شقة للإيجار في بورتسودان",
    city: "بورتسودان",
    area: "الكورنيش",
    price: 6000,
    kind: "rent",
    category: "property",
    grade: "good",
    image: "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
    bedrooms: 2,
    bathrooms: 1,
    size: 95
  },
  {
    id: "9",
    title: "فيلا للإيجار السنوي في كافوري",
    city: "بحري",
    area: "كافوري",
    price: 180000,
    kind: "rent",
    category: "property",
    grade: "excellent",
    image: "https://images.unsplash.com/photo-1613490493576-7fde63acd811?w=800",
    bedrooms: 5,
    bathrooms: 3,
    size: 380
  },
  {
    id: "11",
    title: "استوديو مفروش في الخرطوم 2",
    city: "الخرطوم",
    area: "الرياض",
    price: 4500,
    kind: "rent",
    category: "property",
    grade: "good",
    image: "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800",
    bedrooms: 1,
    bathrooms: 1,
    size: 55
  }
];
export const CITIES = ["الخرطوم", "أم درمان", "بحري", "بورتسودان", "كسلا", "ودمدني", "الأبيض"];
export const CAR_BRANDS = ["تويوتا", "هيونداي", "كيا", "نيسان", "هوندا", "مرسيدس", "BMW"];

export type MockNotification = {
  id: string;
  type: "success" | "warning" | "info";
  title: string;
  desc: string;
  time: string;
  read: boolean;
};

export const MOCK_NOTIFICATIONS: MockNotification[] = [
  { id: "1", type: "success", title: "تم قبول إعلانك", desc: "شقة فاخرة في الخرطوم 2 — تم نشرها في المعرض", time: "منذ ساعة", read: false },
  { id: "2", type: "info", title: "رسالة جديدة", desc: "أرسل إليك أحمد خالد رسالة جديدة", time: "منذ 3 ساعات", read: false },
  { id: "3", type: "warning", title: "يرجى إكمال بياناتك", desc: "الملف الشخصي غير مكتمل", time: "أمس", read: true },
];

export type MockConversation = {
  id: string;
  listingId: string;
  buyerName: string;
  lastMessage: string;
  unread: number;
  time: string;
};

export const MOCK_CONVERSATIONS: MockConversation[] = [
  { id: "1", listingId: "1", buyerName: "أحمد خالد", lastMessage: "هل الإعلان متاح؟", unread: 2, time: "10:30" },
  { id: "2", listingId: "3", buyerName: "سارة محمد", lastMessage: "ما أقل سعر؟", unread: 0, time: "أمس" },
  { id: "3", listingId: "5", buyerName: "عمر علي", lastMessage: "شكراً، سأتصل بك", unread: 0, time: "2025-05-10" },
];
