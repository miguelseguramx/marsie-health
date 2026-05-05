// Convenience aliases for the FHIR R5 types we consume on the client.
// `@types/fhir/r5` ships these as ambient globals under the `fhir5` namespace;
// re-exporting under module-local names keeps imports tidy across the app.

export type Bundle = fhir5.Bundle;
export type BundleEntry = fhir5.BundleEntry;
export type BundleLink = fhir5.BundleLink;
export type BundleEntrySearch = fhir5.BundleEntrySearch;

export type DiagnosticReport = fhir5.DiagnosticReport;
export type Patient = fhir5.Patient;
export type Organization = fhir5.Organization;
export type Observation = fhir5.Observation;
export type Reference = fhir5.Reference;
export type Extension = fhir5.Extension;
export type CodeableConcept = fhir5.CodeableConcept;
export type Quantity = fhir5.Quantity;
export type ObservationReferenceRange = fhir5.ObservationReferenceRange;
export type Identifier = fhir5.Identifier;
export type HumanName = fhir5.HumanName;
export type ContactPoint = fhir5.ContactPoint;
export type ExtendedContactDetail = fhir5.ExtendedContactDetail;
export type OperationOutcome = fhir5.OperationOutcome;

// Marsie-specific identifier and extension URIs (must mirror the backend).
export const PATIENT_FILAXIS_SYSTEM = "https://marsie.health/filaxis";
export const LAB_SLUG_SYSTEM = "https://marsie.health/lab-slug";
export const LAB_REPORT_SYSTEM = "https://marsie.health/lab-report";
export const WBC_SUMMARY_EXTENSION =
  "https://marsie.health/StructureDefinition/wbc-summary";

// HL7 / standard system URIs we look up by.
export const LOINC_SYSTEM = "http://loinc.org";
export const INTERPRETATION_SYSTEM =
  "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation";
