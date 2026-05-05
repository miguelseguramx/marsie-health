import { api } from "./client";
import type { AuthUser, LoginResponse } from "../types/api";

export async function login(email: string, password: string): Promise<LoginResponse> {
  const resp = await api.post<LoginResponse>("/api/auth/login/", { email, password });
  return resp.data;
}

export async function fetchMe(): Promise<AuthUser> {
  const resp = await api.get<AuthUser>("/api/auth/me/");
  return resp.data;
}
