import { describe, expect, it } from "vitest";
import fixture from "./__fixtures__/diagnostic-report-bundle.json";
import { bundleToReportDetail, bundleToReportListPage } from "./adapters";
import type { Bundle } from "./types";

const bundle = fixture as unknown as Bundle;

describe("bundleToReportListPage", () => {
  it("flattens DiagnosticReport entries with patient/lab metadata", () => {
    const page = bundleToReportListPage(bundle);
    expect(page.total).toBe(1);
    expect(page.items).toHaveLength(1);
    const item = page.items[0];
    expect(item.id).toBe("r-1");
    expect(item.patient_filaxis_id).toBe("FXS-0001");
    expect(item.patient_name).toBe("Maria Garcia");
    expect(item.lab_name).toBe("ACME Lab");
    expect(item.report_type).toBe("cbc");
    // FHIR `final` -> our display `processed`.
    expect(item.status).toBe("processed");
    expect(item.uploaded_at).toBe("2026-05-01T10:00:00Z");
    expect(item.processed_at).toBe("2026-05-01T11:00:00Z");
  });

  it("reads the WBC summary extension", () => {
    const [item] = bundleToReportListPage(bundle).items;
    expect(item.wbc_value).toBe("3.2");
    expect(item.wbc_low).toBe(true);
  });

  it("exposes opaque pagination link URLs", () => {
    const page = bundleToReportListPage(bundle);
    expect(page.nextUrl).toBeNull();
    expect(page.previousUrl).toBeNull();
  });
});

describe("bundleToReportDetail", () => {
  it("returns the matched DiagnosticReport with its observations", () => {
    const detail = bundleToReportDetail(bundle);
    expect(detail).not.toBeNull();
    expect(detail!.id).toBe("r-1");
    expect(detail!.cbc_results).toHaveLength(2);
    const wbc = detail!.cbc_results.find((c) => c.analyte_code === "WBC")!;
    expect(wbc.analyte_name).toBe("White blood cells");
    expect(wbc.category).toBe("white_cells");
    expect(wbc.value).toBe("3.2");
    expect(wbc.unit).toBe("10^3/uL");
    expect(wbc.ref_range_low).toBe("4.5");
    expect(wbc.ref_range_high).toBe("11");
    expect(wbc.flag).toBe("low");

    const hgb = detail!.cbc_results.find((c) => c.analyte_code === "HGB")!;
    expect(hgb.category).toBe("red_cells");
    expect(hgb.flag).toBe("normal");
  });
});
