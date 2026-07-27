import axios from "axios";


export const API_BASE_URL =
  (typeof window !== "undefined" && (window as any).__API_BASE__) ||
<<<<<<< HEAD
  (import.meta.env.VITE_API_BASE
    ? `${import.meta.env.VITE_API_BASE}/api/v1`
    : "http://localhost:8000/api/v1");
=======
  "http://localhost:8000/api/v1";
>>>>>>> 3db02792a1be00297c0360e421a4581e204e289b

export const api = axios.create({ baseURL: API_BASE_URL, timeout: 15000 });

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

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: { full_name: string; email: string; phone: string; password: string }) =>
    api.post("/auth/register", data),
};

export const usersApi = {
  me: () => api.get("/users/me"),

  submitKYC: (formData: FormData) =>
  api.post("/kyc/submit", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  }),
};

export const listingsApi = {
  getAll: (params: Record<string, any>) => api.get("/listings/", { params }),
  getOne: (id: string) => api.get(`/listings/${id}`),
  create: (data: { kind?: string; category?: string; listing_type?: string }) =>
    api.post("/listings/", data),
  setPrice: (id: string, price: number) => api.post(`/listings/${id}/set-price`, { price }),
  submitForReview: (id: string) => api.post(`/listings/${id}/submit-for-review`),
  updateDetails: (id: string, details: any) =>
    api.post(`/listings/${id}/update-details`, { details }),
  myListings: () => api.get("/listings/mine"),
};

export const uploadApi = {
  uploadImages: (listingId: string, formData: FormData) =>
    api.post(`/upload/listing/${listingId}/images`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
  getConditionResult: (listingId: string) =>
    api.get(`/upload/listing/${listingId}/condition-result`),
};

export const verificationApi = {
  uploadDocs: (listingId: string, formData: FormData) =>
    api.post(`/verification/${listingId}/upload-documents`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

export const notificationsApi = {
  list: () => api.get("/notifications/"),
  unreadCount: () => api.get("/notifications/unread-count"),
  markRead: (id: string) => api.post(`/notifications/${id}/read`),
  markAllRead: () => api.post("/notifications/read-all"),
};

export const adminApi = {
  getStats: () => api.get("/admin/dashboard-stats"),
  getPendingListings: (page = 1) =>
    api.get("/admin/pending-listings", { params: { page } }),
  approveListing: (listingId: string, adminId: string) =>
    api.post("/admin/approve-listing", { listing_id: listingId, admin_id: adminId }),
  rejectListing: (listingId: string, adminId: string, reason: string) =>
    api.post("/admin/reject-listing", { listing_id: listingId, admin_id: adminId, reason }),
};

