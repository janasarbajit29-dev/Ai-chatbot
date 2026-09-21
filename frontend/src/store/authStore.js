import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  currentUser: null, // { name: string, ... }
  users: [], // Array of registered users
  hasSpokenGreeting: false,

  setHasSpokenGreeting: (val) => set({ hasSpokenGreeting: val }),

  signup: (userData) => {
    set((state) => ({
      users: [...state.users, userData]
    }));
  },

  login: (userData) => {
    set({ currentUser: userData });
    return true;
  },

  logout: () => {
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    set({ currentUser: null, hasSpokenGreeting: false });
  },
}));
