export const setToken = (token) => {
  localStorage.setItem('aura_access_token', token);
};

export const getToken = () => {
  return localStorage.getItem('aura_access_token');
};

export const removeToken = () => {
  localStorage.removeItem('aura_access_token');
};

export const setUser = (user) => {
  localStorage.setItem('aura_user', JSON.stringify(user));
};

export const getUser = () => {
  const user = localStorage.getItem('aura_user');
  return user ? JSON.parse(user) : null;
};

export const removeUser = () => {
  localStorage.removeItem('aura_user');
};
