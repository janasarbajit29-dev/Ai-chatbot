import axios from "axios";
import { getToken } from "../utils/auth";

// Create an Axios instance with base configuration
export const apiClient = axios.create({
  baseURL: `${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 10000,
});

// Add a request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
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
    // Handle global errors here (e.g., redirect to login on 401)
    return Promise.reject(error);
  }
);
