export interface PaginatedResults<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type Role = "Patient" | "Physician" | "LabAdmin";

export interface AuthUser {
  email: string;
  role: Role | null;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  email: string;
  role: Role | null;
}

export interface RefreshResponse {
  access: string;
}

export type ReportStatus = "received" | "processing" | "processed" | "failed";
export type ReportType = "cbc" | string;

export interface ReportListItem {
  id: string;
  patient_name: string;
  patient_filaxis_id: string;
  lab_name: string;
  report_type: ReportType;
  status: ReportStatus;
  uploaded_at: string;
  processed_at: string | null;
  wbc_value: string | null;
  wbc_low: boolean;
}

export type CbcFlag = "low" | "normal" | "high" | "critical";

export interface CbcResult {
  analyte_code: string;
  analyte_name: string;
  category: string;
  value: string;
  unit: string;
  ref_range_low: string | null;
  ref_range_high: string | null;
  flag: CbcFlag;
}

export interface ReportDetail extends ReportListItem {
  cbc_results: CbcResult[];
}

export interface UploadReportResponse {
  report_id: string;
  patient_email: string;
  email_sent: boolean;
}

export interface OnboardingCompleteResponse {
  access: string;
  refresh: string;
  email: string;
  role: Role | null;
  report_id: string | null;
}
