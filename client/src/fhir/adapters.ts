// Adapters that map FHIR R5 Bundles emitted by /fhir/* to the legacy
// display types that `ReportListPage`, `ReportDetailPage`, and `CbcTable`
// already render. Keeping the display contract stable lets us migrate the
// API without churning the UI components.

import type {
  CbcFlag,
  CbcResult,
  ReportDetail,
  ReportListItem,
  ReportStatus,
} from "../types/api";
import { buildResourceMap, resolveReference } from "./resolveReference";
import type {
  Bundle,
  BundleEntry,
  CodeableConcept,
  DiagnosticReport,
  Extension,
  Observation,
  Organization,
  Patient,
  Quantity,
} from "./types";
import {
  INTERPRETATION_SYSTEM,
  PATIENT_FILAXIS_SYSTEM,
  WBC_SUMMARY_EXTENSION,
} from "./types";

// FHIR DiagnosticReport.status -> our legacy ReportStatus.
const FHIR_STATUS_TO_DISPLAY: Record<string, ReportStatus> = {
  registered: "received",
  partial: "processing",
  final: "processed",
  cancelled: "failed",
};

const INTERPRETATION_TO_FLAG: Record<string, CbcFlag> = {
  L: "low",
  N: "normal",
  H: "high",
  // FHIR has no canonical "critical" code; the backend emits `A` (Abnormal)
  // with text="critical". Read the text to disambiguate.
  A: "critical",
};

// Map LOINC codes back to our internal analyte codes for the columns the UI
// renders. Mirror of the seeded Analyte table.
const ANALYTE_BY_LOINC: Record<string, { code: string; category: string; name: string }> = {
  "4544-3": { code: "HCT", category: "red_cells", name: "Hematocrit" },
  "718-7": { code: "HGB", category: "red_cells", name: "Hemoglobin" },
  "789-8": { code: "RBC", category: "red_cells", name: "Red blood cells" },
  "787-2": { code: "MCV", category: "red_indices", name: "Mean corpuscular volume" },
  "785-6": { code: "MCH", category: "red_indices", name: "Mean corpuscular hemoglobin" },
  "786-4": {
    code: "MCHC",
    category: "red_indices",
    name: "Mean corpuscular hemoglobin concentration",
  },
  "788-0": { code: "RDW", category: "red_indices", name: "Red cell distribution width" },
  "6690-2": { code: "WBC", category: "white_cells", name: "White blood cells" },
  "770-8": { code: "NEUT_PCT", category: "white_cells", name: "Neutrophils percent" },
  "736-9": { code: "LYMPH_PCT", category: "white_cells", name: "Lymphocytes percent" },
  "5905-5": { code: "MONO_PCT", category: "white_cells", name: "Monocytes percent" },
  "713-8": { code: "EOS_PCT", category: "white_cells", name: "Eosinophils percent" },
  "706-2": { code: "BASO_PCT", category: "white_cells", name: "Basophils percent" },
  "777-3": { code: "PLT", category: "platelets", name: "Platelets" },
};

// --- helpers ---------------------------------------------------------------

function findExtension(extensions: Extension[] | undefined, url: string): Extension | undefined {
  return extensions?.find((e) => e.url === url);
}

function readWbcSummary(dr: DiagnosticReport): { value: string | null; low: boolean } {
  const ext = findExtension(dr.extension, WBC_SUMMARY_EXTENSION);
  if (!ext?.extension) return { value: null, low: false };
  const valueExt = findExtension(ext.extension, "value");
  const lowExt = findExtension(ext.extension, "low");
  const decimalValue = valueExt?.valueDecimal;
  return {
    value: decimalValue !== undefined ? String(decimalValue) : null,
    low: Boolean(lowExt?.valueBoolean),
  };
}

function patientName(patient: Patient | undefined): string {
  if (!patient?.name?.length) return "";
  const n = patient.name[0];
  const given = (n.given ?? []).join(" ").trim();
  const full = `${given} ${n.family ?? ""}`.trim();
  return full;
}

function filaxisIdFor(patient: Patient | undefined): string {
  const id = patient?.identifier?.find((i) => i.system === PATIENT_FILAXIS_SYSTEM);
  return id?.value ?? "";
}

function organizationName(org: Organization | undefined): string {
  return org?.name ?? "";
}

function quantityToString(q: Quantity | undefined): string {
  if (!q || q.value === undefined || q.value === null) return "";
  return String(q.value);
}

function interpretationToFlag(coding: CodeableConcept[] | undefined): CbcFlag {
  if (!coding?.length) return "normal";
  const cc = coding[0];
  for (const c of cc.coding ?? []) {
    if (c.system === INTERPRETATION_SYSTEM) {
      // `A` is emitted with text="critical" to distinguish from generic abnormal.
      if (c.code === "A" && (cc.text ?? "").toLowerCase() === "critical") return "critical";
      const mapped = INTERPRETATION_TO_FLAG[c.code ?? ""];
      if (mapped) return mapped;
    }
  }
  return "normal";
}

function diagnosticReportToReportListItem(
  dr: DiagnosticReport,
  patient: Patient | undefined,
  org: Organization | undefined,
): ReportListItem {
  const wbc = readWbcSummary(dr);
  return {
    id: dr.id ?? "",
    patient_name: patientName(patient) || filaxisIdFor(patient),
    patient_filaxis_id: filaxisIdFor(patient),
    lab_name: organizationName(org),
    report_type: "cbc",
    status: FHIR_STATUS_TO_DISPLAY[dr.status ?? ""] ?? "received",
    uploaded_at: dr.effectiveDateTime ?? "",
    processed_at: dr.issued ?? null,
    wbc_value: wbc.value,
    wbc_low: wbc.low,
  };
}

function observationToCbcResult(obs: Observation): CbcResult | null {
  const loinc = obs.code?.coding?.find((c) => c.system === "http://loinc.org");
  const meta = loinc?.code ? ANALYTE_BY_LOINC[loinc.code] : undefined;
  const analyteCode = meta?.code ?? loinc?.code ?? obs.code?.text ?? "";
  const analyteName = meta?.name ?? obs.code?.text ?? "";
  const category = meta?.category ?? "";
  const value = obs.valueQuantity;
  if (!value) return null;
  const refRange = obs.referenceRange?.[0];
  return {
    analyte_code: analyteCode,
    analyte_name: analyteName,
    category,
    value: quantityToString(value),
    unit: value.unit ?? "",
    ref_range_low: refRange?.low ? quantityToString(refRange.low) : null,
    ref_range_high: refRange?.high ? quantityToString(refRange.high) : null,
    flag: interpretationToFlag(obs.interpretation),
  };
}

// --- public adapters -------------------------------------------------------

export interface ReportListPage {
  total: number;
  items: ReportListItem[];
  // Opaque next/prev link URLs (or null) — follow them verbatim.
  nextUrl: string | null;
  previousUrl: string | null;
}

export function bundleToReportListPage(bundle: Bundle): ReportListPage {
  const map = buildResourceMap(bundle);
  const items: ReportListItem[] = [];
  for (const entry of bundle.entry ?? []) {
    if (entry.search?.mode !== "match") continue;
    const dr = entry.resource as DiagnosticReport | undefined;
    if (!dr || dr.resourceType !== "DiagnosticReport") continue;
    const patient = resolveReference<Patient>(map, dr.subject);
    const org = resolveReference<Organization>(map, dr.performer?.[0]);
    items.push(diagnosticReportToReportListItem(dr, patient, org));
  }
  return {
    total: bundle.total ?? items.length,
    items,
    nextUrl: linkUrl(bundle, "next"),
    previousUrl: linkUrl(bundle, "previous"),
  };
}

export function bundleToReportDetail(bundle: Bundle): ReportDetail | null {
  const map = buildResourceMap(bundle);
  const matchEntry: BundleEntry | undefined = bundle.entry?.find(
    (e) =>
      e.search?.mode === "match" &&
      (e.resource as DiagnosticReport | undefined)?.resourceType === "DiagnosticReport",
  );
  const dr = matchEntry?.resource as DiagnosticReport | undefined;
  if (!dr) return null;
  const patient = resolveReference<Patient>(map, dr.subject);
  const org = resolveReference<Organization>(map, dr.performer?.[0]);
  const list = diagnosticReportToReportListItem(dr, patient, org);
  const cbc_results = observationsForReport(bundle, dr);
  return { ...list, cbc_results };
}

function observationsForReport(bundle: Bundle, dr: DiagnosticReport): CbcResult[] {
  const map = buildResourceMap(bundle);
  const observations: Observation[] = [];
  // Prefer DiagnosticReport.result references; fall back to all included
  // Observations if `result` is missing.
  if (dr.result?.length) {
    for (const ref of dr.result) {
      const obs = resolveReference<Observation>(map, ref);
      if (obs && obs.resourceType === "Observation") observations.push(obs);
    }
  } else {
    for (const entry of bundle.entry ?? []) {
      const r = entry.resource as Observation | undefined;
      if (r?.resourceType === "Observation") observations.push(r);
    }
  }
  return observations
    .map(observationToCbcResult)
    .filter((x): x is CbcResult => x !== null)
    .sort((a, b) => {
      if (a.category === b.category) return a.analyte_code.localeCompare(b.analyte_code);
      return a.category.localeCompare(b.category);
    });
}

function linkUrl(bundle: Bundle, relation: string): string | null {
  const link = bundle.link?.find((l) => l.relation === relation);
  return link?.url ?? null;
}
