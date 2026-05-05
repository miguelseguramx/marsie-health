import { useQuery } from "@tanstack/react-query";
import { getReport, listReports, type ListReportsParams } from "../api/reports";
import type { PaginatedResults, ReportDetail, ReportListItem } from "../types/api";

export function useReports(params: ListReportsParams) {
  return useQuery<PaginatedResults<ReportListItem>, Error>({
    queryKey: ["reports", params],
    queryFn: () => listReports(params),
    placeholderData: (prev) => prev,
  });
}

export function useReport(id: string | undefined) {
  return useQuery<ReportDetail, Error>({
    queryKey: ["reports", id],
    queryFn: () => getReport(id as string),
    enabled: Boolean(id),
  });
}
