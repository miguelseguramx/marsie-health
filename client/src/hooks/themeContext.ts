import { createContext } from "react";
import type { ThemeMode } from "../utils/theme";

export interface ThemeContextValue {
  mode: ThemeMode;
  toggle: () => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);
