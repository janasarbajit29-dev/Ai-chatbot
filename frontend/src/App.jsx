import { useEffect, useState, useRef } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { getAccessToken } from "./utils/auth";
import { useAuthStore } from "./store/authStore";
import { apiClient } from "./lib/axios";
import { AIAvatar } from "./components/core/AIAvatar";
import { AnimatedBackground } from "./components/core/AnimatedBackground";
import { AnimatePresence, motion } from "framer-motion";

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const loginSuccess = useAuthStore((state) => state.loginSuccess);
  const logout = useAuthStore((state) => state.logout);
  const setSessionExpiredMessage = useAuthStore((state) => state.setSessionExpiredMessage);
  
  useEffect(() => {
    const controller = new AbortController();
    
    const restoreSession = async () => {
      const token = getAccessToken();
      if (!token) {
        setIsAuthLoading(false);
        return;
      }

      try {
        const response = await apiClient.get("/api/auth/me", {
          signal: controller.signal
        });
        if (response.status === 200) {
          loginSuccess(response.data, token);
        }
      } catch (error) {
        if (error.name === "CanceledError" || error.message === "canceled" || error.code === "ERR_CANCELED") {
          // React StrictMode or unmount aborted this request. Do not update state.
          return;
        }
        
        if (!error.response) {
          // Network error: do not silently delete potentially valid token.
          console.error("Network error during session restoration.");
        } else if (error.response.status === 401) {
          // Check if it's the 5-day expiration
          const detail = error.response.data?.detail;
          logout();
          if (typeof detail === "string" && detail.includes("5 days of inactivity")) {
            setSessionExpiredMessage("Your session expired. Please log in again.");
          }
        }
      } finally {
        if (!controller.signal.aborted) {
          setIsAuthLoading(false);
        }
      }
    };

    restoreSession();
    
    return () => {
      controller.abort();
    };
  }, [loginSuccess, logout, setSessionExpiredMessage]);

  if (isAuthLoading) {
    return (
      <div className="relative h-screen bg-canvas flex flex-col items-center justify-center overflow-hidden">
        <AnimatedBackground />
        <AnimatePresence>
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="z-10 flex flex-col items-center"
          >
            <AIAvatar size="large" state="idle" />
            <p className="mt-8 text-text-secondary font-medium tracking-wide animate-pulse">
              Restoring Workspace...
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;
