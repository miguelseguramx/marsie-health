import { createContext } from "react";
import type { AuthUser, LoginResponse, Role } from "../types/api";

export interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<LoginResponse>;
  logout: () => void;
  setSession: (access: string, refresh: string, email: string, role: Role | null) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
