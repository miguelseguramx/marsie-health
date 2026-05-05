import { useState } from "react";
import { Card, Form, Input, Button, Alert, Typography } from "antd";
import { Link, useNavigate, useParams } from "react-router-dom";
import { AxiosError } from "axios";
import { useAuth } from "../hooks/useAuth";
import { completeOnboarding } from "../api/labAdmin";
import logoMarsie from "../assets/logo-marsie.svg";

interface FormValues {
  password: string;
  confirm: string;
}

export function OnboardingPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { setSession } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onFinish = async (values: FormValues) => {
    if (!token) {
      setError("Missing onboarding token.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const data = await completeOnboarding(token, values.password);
      setSession(data.access, data.refresh, data.email, data.role);
      navigate(data.report_id ? `/results/${data.report_id}` : "/results", { replace: true });
    } catch (err) {
      const detail =
        err instanceof AxiosError ? err.response?.data?.detail : undefined;
      setError(detail ?? "Could not complete onboarding. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-page__card">
        <img src={logoMarsie} alt="marsie" className="login-page__logo" />
        <Typography.Paragraph type="secondary">
          Welcome — set a password to view your report.
        </Typography.Paragraph>

        {error && (
          <Alert
            type="error"
            message={error}
            className="login-page__alert"
            showIcon
            action={
              <Link to="/login">
                <Button size="small">Sign in</Button>
              </Link>
            }
          />
        )}

        <Form<FormValues> layout="vertical" onFinish={onFinish} requiredMark={false}>
          <Form.Item
            label="Password"
            name="password"
            rules={[
              { required: true, message: "Please enter a password" },
              { min: 8, message: "Password must be at least 8 characters" },
            ]}
            hasFeedback
          >
            <Input.Password autoComplete="new-password" autoFocus />
          </Form.Item>
          <Form.Item
            label="Confirm password"
            name="confirm"
            dependencies={["password"]}
            hasFeedback
            rules={[
              { required: true, message: "Please confirm your password" },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) return Promise.resolve();
                  return Promise.reject(new Error("Passwords do not match"));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Set password and continue
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
