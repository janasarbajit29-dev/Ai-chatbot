import { create } from 'zustand';
import { setAccessToken, setStoredUser, clearAuthStorage } from '../utils/auth';

export const useAuthStore = create((set) => ({
  isAuthenticated: false,
  currentUser: null, // { id: number, name: string, email: string }
  accessToken: null,
  sessionExpiredMessage: null,
  hasSpokenGreeting: false,

  setSessionExpiredMessage: (msg) => set({ sessionExpiredMessage: msg }),
  setHasSpokenGreeting: (val) => set({ hasSpokenGreeting: val }),

  loginSuccess: (user, token) => {
    setAccessToken(token);
    setStoredUser(user);
    
    // Ensure we only store safe fields in state
    const safeUser = { id: user.id, name: user.name, email: user.email };
    set({ isAuthenticated: true, currentUser: safeUser, accessToken: token, sessionExpiredMessage: null, hasSpokenGreeting: false });
  },

  logout: () => {
    clearAuthStorage();
    if (typeof window !== "undefined" && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    set({ isAuthenticated: false, currentUser: null, accessToken: null, hasSpokenGreeting: false });
  },
}));
