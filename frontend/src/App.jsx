import { useEffect, useState, useRef } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { apiClient } from "./lib/axios";
import { useAuthStore } from "./store/authStore";
import { getToken, removeToken, removeUser, setUser } from "./utils/auth";

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
  const login = useAuthStore((state) => state.login);
  const hasFetched = useRef(false);

  useEffect(() => {
    const restoreSession = async () => {
      const token = getToken();
      if (!token) {
        setIsAuthLoading(false);
        return;
      }

      if (hasFetched.current) return;
      hasFetched.current = true;

      try {
        const response = await apiClient.get("/auth/me");
        setUser(response.data);
        login(response.data);
      } catch (error) {
        if (error.response && error.response.status === 401) {
          removeToken();
          removeUser();
        }
        // If network error, we do not remove token.
      } finally {
        setIsAuthLoading(false);
      }
    };

    restoreSession();
  }, [login]);

  if (isAuthLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-zinc-900 text-white text-xl">
        Restoring Workspace...
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
