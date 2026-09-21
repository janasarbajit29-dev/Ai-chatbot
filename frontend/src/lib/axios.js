import axios from "axios";
import { getAccessToken } from "../utils/auth";
import { useAuthStore } from "../store/authStore";

// Create an Axios instance with base configuration
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Basic centralized error handling
    if (!error.response) {
      // Network error or backend unavailable
      console.error("Network error or Backend unavailable:", error.message);
    } else {
      // HTTP error response from backend
      console.error(`HTTP error response [${error.response.status}]:`, error.response.data);
      
      // Global 401 handling (exclude login endpoint)
      if (error.response.status === 401) {
        const isLoginRequest = error.config?.url?.includes("/api/auth/login");
        if (!isLoginRequest) {
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  }
);
