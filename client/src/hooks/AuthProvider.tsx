import { useCallback, useMemo, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchMe, login as loginRequest } from "../api/auth";
import { tokens } from "../api/tokens";
import type { AuthUser, LoginResponse, Role } from "../types/api";
import { AuthContext, type AuthContextValue } from "./authContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const hasTokens = Boolean(tokens.getAccess() && tokens.getRefresh());

  const meQuery = useQuery<AuthUser, Error>({
    queryKey: ["auth", "me"],
    queryFn: fetchMe,
    enabled: hasTokens,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });

  const loginMutation = useMutation<LoginResponse, Error, { email: string; password: string }>({
    mutationFn: ({ email, password }) => loginRequest(email, password),
    onSuccess: (data) => {
      tokens.set(data.access, data.refresh);
      queryClient.setQueryData<AuthUser>(["auth", "me"], { email: data.email, role: data.role });
    },
  });

  const login = useCallback(
    (email: string, password: string) => loginMutation.mutateAsync({ email, password }),
    [loginMutation],
  );

  const logout = useCallback(() => {
    tokens.clear();
    queryClient.clear();
  }, [queryClient]);

  const setSession = useCallback(
    (access: string, refresh: string, email: string, role: Role | null) => {
      tokens.set(access, refresh);
      queryClient.setQueryData<AuthUser>(["auth", "me"], { email, role });
    },
    [queryClient],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user: meQuery.data ?? null,
      isLoading: hasTokens && meQuery.isLoading,
      isAuthenticated: Boolean(meQuery.data),
      login,
      logout,
      setSession,
    }),
    [meQuery.data, meQuery.isLoading, hasTokens, login, logout, setSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
