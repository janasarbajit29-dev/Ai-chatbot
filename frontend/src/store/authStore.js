import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  currentUser: null, // { name: string, ... }
  users: [], // Array of registered users

  signup: (userData) => {
    set((state) => ({
      users: [...state.users, userData]
    }));
  },

  login: (name, password) => {
    const { users } = get();
    const foundUser = users.find(u => u.name === name && u.password === password);
    
    if (foundUser) {
      set({ currentUser: foundUser });
      return true;
    }
    return false;
  },

  logout: () => set({ currentUser: null }),
}));
