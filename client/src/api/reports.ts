import { api } from "./client";
import { bundleToReportDetail, bundleToReportListPage } from "../fhir/adapters";
import type { Bundle } from "../fhir/types";
import type { PaginatedResults, ReportDetail, ReportListItem } from "../types/api";

export interface ListReportsParams {
  page?: number;
  pageSize?: number;
  ordering?: string;
}

// Map legacy ORM-style ordering tokens (used by the antd Table sorters) to
// FHIR R5 _sort tokens. Unknown tokens fall back to the default sort so the
// UI never trips on a server-rejected param.
const ORDERING_TO_FHIR_SORT: Record<string, string> = {
  uploaded_at: "_lastUpdated",
  "-uploaded_at": "-_lastUpdated",
  status: "status",
  "-status": "-status",
  patient__filaxis_id: "subject",
  "-patient__filaxis_id": "-subject",
};

const DEFAULT_FHIR_SORT = "-_lastUpdated";

function fhirSortFor(ordering: string | undefined): string {
  if (!ordering) return DEFAULT_FHIR_SORT;
  return ORDERING_TO_FHIR_SORT[ordering] ?? DEFAULT_FHIR_SORT;
}

export async function listReports(
  params: ListReportsParams = {},
): Promise<PaginatedResults<ReportListItem>> {
  const resp = await api.get<Bundle>("/fhir/DiagnosticReport", {
    params: {
      page: params.page,
      _count: params.pageSize,
      _sort: fhirSortFor(params.ordering),
    },
    headers: { Accept: "application/fhir+json" },
  });
  const page = bundleToReportListPage(resp.data);
  return {
    count: page.total,
    next: page.nextUrl,
    previous: page.previousUrl,
    results: page.items,
  };
}

export async function getReport(id: string): Promise<ReportDetail> {
  const resp = await api.get<Bundle>(`/fhir/DiagnosticReport/${id}`, {
    headers: { Accept: "application/fhir+json" },
  });
  const detail = bundleToReportDetail(resp.data);
  if (!detail) {
    throw new Error("Bundle did not contain a matching DiagnosticReport");
  }
  return detail;
}
