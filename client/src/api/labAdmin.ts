import { api } from "./client";
import type { OnboardingCompleteResponse, UploadReportResponse } from "../types/api";

export interface UploadReportInput {
  patient_email: string;
  patient_first_name: string;
  patient_last_name: string;
  file?: File | null;
}

export async function uploadReport(input: UploadReportInput): Promise<UploadReportResponse> {
  const fd = new FormData();
  fd.append("patient_email", input.patient_email);
  fd.append("patient_first_name", input.patient_first_name);
  fd.append("patient_last_name", input.patient_last_name);
  if (input.file) fd.append("file", input.file);
  const resp = await api.post<UploadReportResponse>("/api/lab-admin/reports/", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return resp.data;
}

export async function completeOnboarding(
  token: string,
  password: string,
): Promise<OnboardingCompleteResponse> {
  const resp = await api.post<OnboardingCompleteResponse>(
    "/api/auth/onboarding/complete/",
    { token, password },
  );
  return resp.data;
}
