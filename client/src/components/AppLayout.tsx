import { Layout, Button } from "antd";
import { MoonOutlined, SunOutlined } from "@ant-design/icons";
import { Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../hooks/useTheme";
import logoMarsie from "../assets/logo-marsie.svg";

const { Header, Content } = Layout;

const ROLE_LABEL: Record<string, string> = {
  Patient: "Patient",
  Physician: "Physician",
  LabAdmin: "Lab admin",
};

export function AppLayout() {
  const { user, logout } = useAuth();
  const { mode, toggle } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <Layout className="app-layout">
      <Header className="app-layout__header">
        <div className="app-layout__brand">
          <img src={logoMarsie} alt="marsie" className="app-layout__brand-logo" />
        </div>
        <div className="app-layout__user">
          {user && (
            <>
              <span className="app-layout__role">
                {user.role ? ROLE_LABEL[user.role] : "No role"}
              </span>
              <span className="app-layout__email">{user.email}</span>
            </>
          )}
          <Button
            type="text"
            icon={mode === "dark" ? <SunOutlined /> : <MoonOutlined />}
            onClick={toggle}
            aria-label="Toggle theme"
          />
          <Button type="default" onClick={handleLogout}>
            Sign out
          </Button>
        </div>
      </Header>
      <Content className="app-layout__content">
        <Outlet />
      </Content>
    </Layout>
  );
}
