import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { tokens } from "./tokens";
import type { RefreshResponse } from "../types/api";

export const api = axios.create({
  baseURL: "/",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const access = tokens.getAccess();
  if (access && config.headers) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccess(): Promise<string | null> {
  const refresh = tokens.getRefresh();
  if (!refresh) return null;
  try {
    const resp = await axios.post<RefreshResponse>(
      "/api/auth/refresh/",
      { refresh },
      { headers: { "Content-Type": "application/json" } },
    );
    tokens.setAccess(resp.data.access);
    return resp.data.access;
  } catch {
    tokens.clear();
    return null;
  }
}

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.response.use(
  (resp) => resp,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const status = error.response?.status;

    if (status !== 401 || !original || original._retry) {
      return Promise.reject(error);
    }

    const url = original.url ?? "";
    if (url.includes("/auth/login") || url.includes("/auth/refresh")) {
      return Promise.reject(error);
    }

    original._retry = true;
    refreshing ??= refreshAccess().finally(() => {
      refreshing = null;
    });
    const newAccess = await refreshing;
    if (!newAccess) {
      return Promise.reject(error);
    }
    if (original.headers) {
      original.headers.Authorization = `Bearer ${newAccess}`;
    }
    return api(original);
  },
);
