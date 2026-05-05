import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ConfigProvider, theme as antdTheme } from "antd";
import enUS from "antd/locale/en_US";
import { AuthProvider } from "./hooks/AuthProvider";
import { ThemeProvider } from "./hooks/ThemeProvider";
import { useTheme } from "./hooks/useTheme";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AppLayout } from "./components/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { OnboardingPage } from "./pages/OnboardingPage";
import { ReportListPage } from "./pages/ReportListPage";
import { ReportDetailPage } from "./pages/ReportDetailPage";
import { NotFoundPage } from "./pages/NotFoundPage";

function ThemedApp() {
  const { mode } = useTheme();
  const theme = {
    algorithm: mode === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
    token: {
      colorPrimary: "#2563eb",
      fontFamily:
        "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    },
  };

  return (
    <ConfigProvider locale={enUS} theme={theme}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/onboarding/:token" element={<OnboardingPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Navigate to="/results" replace />} />
              <Route path="/results" element={<ReportListPage />} />
              <Route path="/results/:id" element={<ReportDetailPage />} />
            </Route>
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <ThemedApp />
    </ThemeProvider>
  );
}
