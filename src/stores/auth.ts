import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role?: "user" | "admin" | "super_admin";
  admin_role?: "super_admin" | "admin" | "moderator" | "reviewer" | null;
}

interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isLoggedIn: boolean;
  login: (user: AuthUser, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoggedIn: false,
      login: (user, token) => {
        if (typeof window !== "undefined") localStorage.setItem("tm_token", token);
        set({ user, token, isLoggedIn: true });
      },
      logout: () => {
        if (typeof window !== "undefined") localStorage.removeItem("tm_token");
        set({ user: null, token: null, isLoggedIn: false });
      },
    }),
    { name: "tm_auth" },
  ),
);
