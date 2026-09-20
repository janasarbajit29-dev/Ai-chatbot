const TOKEN_KEY = 'aura_access_token';
const USER_KEY = 'aura_user';

export const getAccessToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

export const setAccessToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
};

export const removeAccessToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

export const getStoredUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error('Invalid user data in storage. Clearing auth storage.');
    clearAuthStorage();
    return null;
  }
};

export const setStoredUser = (user) => {
  if (user) {
    // Only store safe fields
    const safeUser = {
      id: user.id,
      name: user.name,
      email: user.email,
    };
    localStorage.setItem(USER_KEY, JSON.stringify(safeUser));
  }
};

export const removeStoredUser = () => {
  localStorage.removeItem(USER_KEY);
};

export const clearAuthStorage = () => {
  removeAccessToken();
  removeStoredUser();
};
