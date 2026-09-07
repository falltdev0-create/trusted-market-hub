import axios from "axios";

export const API_BASE_URL =
  (typeof window !== "undefined" && (window as any).__API_BASE__) ||
  "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 30000 });

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("tm_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const status = error.response?.status;
    if (status === 401 && typeof window !== "undefined") {
      const path = window.location.pathname;
      if (path !== "/login" && path !== "/register") {
        localStorage.removeItem("tm_token");
      }
    }
    return Promise.reject(error);
  },
);

/** Try API call; on network/5xx error return fallback (keeps UI functional offline). */
export async function tryApi<T>(fn: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await fn();
  } catch (e: any) {
    if (!e?.response || e.response.status >= 500) return fallback;
    throw e;
  }
}

/** رسالة خطأ عربية مقروءة من أي استجابة خطأ */
export function apiError(e: any, fallback = "حدث خطأ غير متوقع"): string {
  const d = e?.response?.data?.detail ?? e?.response?.data?.message;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x: any) => x?.msg || x?.message).filter(Boolean).join("، ") || fallback;
  if (d && typeof d === "object") return d.message || fallback;
  if (!e?.response) return "تعذّر الاتصال بالخادم";
  return fallback;
}

export const authApi = {
  login: (email: string, password: string) => api.post("/auth/login", { email, password }),
  register: (data: { full_name: string; email: string; phone: string; password: string }) =>
    api.post("/auth/register", data),
};

export const usersApi = {
  me: () => api.get("/users/me"),
  startKyc: () => api.post("/kyc/start"),
  kycStatus: () => api.get("/kyc/status"),
  submitKYC: (formData: FormData) =>
    api.post("/kyc/submit", formData, { headers: { "Content-Type": "multipart/form-data" } }),
  uploadAvatar: (formData: FormData) =>
    api.post("/users/me/avatar", formData, { headers: { "Content-Type": "multipart/form-data" } }),
};

export const listingsApi = {
  getAll: (params: Record<string, any>) => api.get("/listings/", { params }),
  getOne: (id: string) => api.get(`/listings/${id}`),
  create: (data: Record<string, any>) => api.post("/listings/", data),
  setPrice: (id: string, price: number) => api.post(`/listings/${id}/set-price`, { price }),
  submitForReview: (id: string) => api.post(`/listings/${id}/submit-for-review`),
  updateDetails: (id: string, details: any) => api.post(`/listings/${id}/update-details`, { details }),
  myListings: () => api.get("/listings/mine"),
  remove: (id: string) => api.delete(`/listings/${id}`),
};

export const uploadApi = {
  uploadImages: (listingId: string, formData: FormData) =>
    api.post(`/upload/listing/${listingId}/images`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    }),
  getConditionResult: (listingId: string) => api.get(`/upload/listing/${listingId}/condition-result`),
};

export const verificationApi = {
  uploadDocs: (listingId: string, formData: FormData) =>
    api.post(`/verification/${listingId}/upload-documents`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    }),
  status: (listingId: string) => api.get(`/verification/${listingId}/verification-status`),
};

export const notificationsApi = {
  list: () => api.get("/notifications/"),
  unreadCount: () => api.get("/notifications/unread-count"),
  markRead: (id: string) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
};

export const ragApi = {
  status: () => api.get("/rag/status"),
  search: (query: string, top_k = 5) => api.post("/rag/search", { query, top_k }).then((r) => r.data),
  ask: (question: string, top_k = 5) => api.post("/rag/ask", { question, top_k }).then((r) => r.data),
  indexListings: () => api.post("/rag/index/listings").then((r) => r.data),
  indexDoc: (payload: { source?: string; title?: string; content: string }) =>
    api.post("/rag/index", payload).then((r) => r.data),
};

export const adminApi = {
  // إحصائيات
  getStats: () => api.get("/admin/dashboard-stats"),

  // الإعلانات
  getListings: (params: { status?: string; q?: string; page?: number; page_size?: number } = {}) =>
    api.get("/admin/listings", { params }),
  getPendingListings: (page = 1) => api.get("/admin/pending-listings", { params: { page } }),
  getListing: (id: string) => api.get(`/admin/listing/${id}/full-review`),
  approveListing: (listingId: string) => api.post("/admin/approve-listing", { listing_id: listingId }),
  rejectListing: (listingId: string, reason: string) =>
    api.post("/admin/reject-listing", { listing_id: listingId, reason }),
  deleteListing: (id: string) => api.delete(`/admin/listing/${id}`),

  // المستخدمون
  getUsers: (params: { q?: string; role?: string; page?: number } = {}) =>
    api.get("/admin/users", { params }),
  updateUser: (id: string, data: Record<string, any>) => api.patch(`/admin/users/${id}`, data),
  banUser: (id: string, banned: boolean) => api.post(`/admin/users/${id}/ban`, { banned }),
  deleteUser: (id: string) => api.delete(`/admin/users/${id}`),

  // طلبات التحقق (KYC)
  getKycRequests: (status = "pending") => api.get("/admin/kyc-requests", { params: { status } }),
  approveKyc: (userId: string) => api.post(`/admin/kyc/${userId}/approve`),
  rejectKyc: (userId: string, reason: string) => api.post(`/admin/kyc/${userId}/reject`, { reason }),

  // سجل التدقيق والإعدادات
  getAuditLogs: (page = 1) => api.get("/admin/audit-logs", { params: { page } }),
  getSettings: () => api.get("/admin/settings"),
  updateSettings: (settings: Record<string, any>) => api.put("/admin/settings", { settings }),
};
