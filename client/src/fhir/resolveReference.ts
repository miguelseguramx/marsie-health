// Tiny helper for resolving FHIR References against a Bundle.
// Hand-rolled to avoid pulling in fhirpath (a 200KB+ dep we don't need).

import type { Bundle, Reference } from "./types";

type AnyResource = { resourceType: string; id?: string };

export type ResourceMap = Map<string, AnyResource>;

export function buildResourceMap(bundle: Bundle | undefined | null): ResourceMap {
  const map: ResourceMap = new Map();
  if (!bundle?.entry) return map;
  for (const entry of bundle.entry) {
    const resource = entry.resource as AnyResource | undefined;
    if (!resource?.resourceType || !resource.id) continue;
    map.set(`${resource.resourceType}/${resource.id}`, resource);
  }
  return map;
}

export function resolveReference<T extends AnyResource = AnyResource>(
  map: ResourceMap,
  ref: Reference | undefined,
): T | undefined {
  if (!ref?.reference) return undefined;
  // FHIR References can be absolute URLs (http://host/Patient/abc) or
  // relative (Patient/abc). Strip everything before the resource type.
  const value = ref.reference;
  const slash = value.lastIndexOf("/");
  if (slash <= 0) return undefined;
  const resourceType = value.substring(0, slash).split("/").pop() ?? "";
  const id = value.substring(slash + 1);
  return map.get(`${resourceType}/${id}`) as T | undefined;
}
