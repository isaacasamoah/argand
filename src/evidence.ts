export type EvidenceRecord = {
  id: string;
  record_key?: string;
  student: string;
  tutor: string;
  tutor_source: string;
  action: string;
  mode?: string;
  evidence: Record<string, string>;
};
export function mergeRecords(
  previous: EvidenceRecord[],
  next: EvidenceRecord[],
) {
  const merged = new Map(previous.map((r) => [r.record_key || r.id, r]));
  for (const record of next) merged.set(record.record_key || record.id, record);
  return [...merged.values()];
}
export type Annotation = {
  error?: string;
  source?: string;
  statement?: string;
  classification?: string;
  citations?: { id: string; quote: string }[];
};
export type Row = {
  id: string;
  title: string;
  requirement: string;
  state: "pass" | "fail" | "uncertain" | "not_applicable";
  probability: number | null;
  annotation?: Annotation;
};
export type Evaluation = { rows: Row[] };

export function counts(rows: Row[]) {
  return {
    pass: rows.filter((r) => r.state === "pass").length,
    fail: rows.filter((r) => r.state === "fail").length,
    uncertain: rows.filter((r) => r.state === "uncertain").length,
  };
}
