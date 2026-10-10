import { counts } from "./evidence";
import type { EvidenceRecord, Evaluation } from "./evidence";
const symbol = (state: string) =>
  state === "pass" ? "✓" : state === "fail" ? "✗" : "•";
export function EvidenceResponse({
  record,
  evaluation,
  error,
}: {
  record: EvidenceRecord;
  evaluation?: Evaluation;
  error?: string;
}) {
  const rows =
      evaluation?.rows.filter((r) => r.state !== "not_applicable") || [],
    c = counts(rows);
  const state = c.fail ? "fail" : c.uncertain ? "uncertain" : "pass";
  return (
    <details className="evidence-response" key={record.id}>
      <summary>
        {evaluation ? symbol(state) : "○"}{" "}
        {record.action === "voice"
          ? `Voice · ${record.mode}`
          : "Answer feedback"}{" "}
        ·{" "}
        {evaluation
          ? `${c.pass} passed, ${c.fail} failed, ${c.uncertain} uncertain`
          : "Not assessed"}
        <span>
          {record.tutor.slice(0, 90)}
          {record.tutor.length > 90 ? "…" : ""}
        </span>
      </summary>
      <p>
        <b>Learner:</b> {record.student || "(No preceding learner transcript)"}
      </p>
      <p>
        <b>Argand:</b> {record.tutor}
      </p>
      <small>{record.tutor_source}</small>
      <details>
        <summary>What was checked</summary>
        {Object.entries(record.evidence).map(([id, text]) => (
          <div key={id}>
            <b>{id}</b>
            <pre>{text}</pre>
          </div>
        ))}
      </details>
      {error && <p role="alert">{error}</p>}
      {rows.map((row) => (
        <div className="evidence-check" key={row.id}>
          <div>
            <strong aria-label={row.state}>{symbol(row.state)}</strong>{" "}
            {row.title}{" "}
            <small>
              {Math.round((row.probability || 0) * 100)}% probability of passing
              {row.state === "uncertain" ? " · uncertain" : ""}
            </small>
          </div>
          {row.annotation && (
            <details>
              <summary>Review the evidence</summary>
              <p>{row.annotation.error || row.annotation.statement}</p>
              {row.annotation.classification && (
                <small>
                  {row.annotation.classification.replaceAll("_", " ")} ·{" "}
                  {row.annotation.source}
                </small>
              )}
              {row.annotation.citations?.map((c, i) => (
                <blockquote key={i}>
                  <b>{c.id}</b> {c.quote}
                </blockquote>
              ))}
            </details>
          )}
        </div>
      ))}
    </details>
  );
}
