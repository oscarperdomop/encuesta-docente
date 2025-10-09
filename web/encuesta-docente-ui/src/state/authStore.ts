import { create } from "zustand";
import { persist } from "zustand/middleware";

type User = { id: string; email: string; nombre?: string; roles?: string[] };

type AuthState = {
  user: User | null;
  setUser: (u: User | null) => void;
  clear: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      setUser: (u) => set({ user: u }),
      clear: () => set({ user: null }),
    }),
    { name: "usco-auth" }
  )
);
