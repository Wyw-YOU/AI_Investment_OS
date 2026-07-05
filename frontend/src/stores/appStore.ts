import { create } from "zustand";

interface AppState {
  currentStock: string;
  setCurrentStock: (code: string) => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  currentStock: "600519",
  setCurrentStock: (code) => set({ currentStock: code }),
  darkMode: false,
  toggleDarkMode: () => set((s) => {
    const next = !s.darkMode;
    document.documentElement.classList.toggle("dark", next);
    return { darkMode: next };
  }),
}));
