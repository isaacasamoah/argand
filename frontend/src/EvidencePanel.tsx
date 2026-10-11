import { api } from "./api";
import type { EvidenceRecord, Evaluation } from "./evidence";
import { EvidenceResponse } from "./EvidenceResponse";
import { EvaluationSummary } from "./EvaluationSummary";
import { useEffect, useRef, useState } from "react";
export function EvidencePanel({
  records,
  open,
  onToggle,
  available,
  capture,
  autoEvaluate,
}: {
  records: EvidenceRecord[];
  open: boolean;
  onToggle: (open: boolean) => void;
  available: boolean;
  capture: () => Promise<EvidenceRecord[]>;
  autoEvaluate: number;
}) {
  const [results, setResults] = useState<Record<string, Evaluation>>({}),
    [errors, setErrors] = useState<Record<string, string>>({}),
    [busy, setBusy] = useState(false),
    [fixture, setFixture] = useState<EvidenceRecord>(),
    [message, setMessage] = useState("");
  const running = useRef(false),
    automatic = useRef(0);
  async function check(items: EvidenceRecord[]) {
    for (const record of items) {
      setErrors((old) => ({ ...old, [record.id]: "" }));
      try {
        const result = await api<Evaluation>(
          `attempts/${record.id}/evaluate`,
          {},
        );
        setResults((old) => ({ ...old, [record.id]: result }));
      } catch (e) {
        setErrors((old) => ({ ...old, [record.id]: (e as Error).message }));
      }
    }
  }
  async function evaluate() {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setMessage("");
    onToggle(true);
    try {
      let current = records;
      try {
        current = await capture();
      } catch (e) {
        setMessage((e as Error).message);
      }
      if (!current.length)
        setMessage(
          (previous) => previous || "No tutor responses to evaluate yet.",
        );
      await check(current.filter((r) => !results[r.id]));
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  useEffect(() => {
    if (autoEvaluate > automatic.current && !busy && available) {
      automatic.current = autoEvaluate;
      void evaluate();
    }
  }, [autoEvaluate, busy, available]);
  async function example() {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    onToggle(true);
    try {
      const record =
        fixture ||
        (await api<EvidenceRecord>("attempts", {
          problem_id: "roots-8",
          action: "failure_fixture",
        }));
      setFixture(record);
      await check([record]);
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  const evaluated = records.filter((r) => results[r.id]);
  return (
    <section className="inline-evidence">
      <button
        className="outline"
        disabled={busy || !available}
        onClick={evaluate}
      >
        {busy ? "Evaluating…" : "Evaluate"}
      </button>
      {open && (
        <>
          <EvaluationSummary
            title="Overall results"
            rows={evaluated.flatMap((r) => results[r.id].rows)}
            assessed={evaluated.length}
            total={records.length}
          />
          {message && <p role="status">{message}</p>}
          <details className="evaluation-turns">
            <summary>Turn-by-turn results</summary>
            {records.map((record) => (
              <EvidenceResponse
                key={record.id}
                record={record}
                evaluation={results[record.id]}
                error={errors[record.id]}
              />
            ))}
          </details>
          <p className="evaluation-method">
            We capture the tutor’s replies, the lesson state and any SymPy maths
            checks, then ask Jev (TypeSafe’s <b>jev-1.13.0</b> model for
            structured judgments) how likely each teaching requirement is to be
            satisfied. Below 35% is a fail, 35–65% is uncertain, and above 65%
            is a pass. <b>GPT-6.1-Sol</b> provides tutor reasoning, written
            feedback and evidence annotations for failed or uncertain checks;{" "}
            <b>GPT-Live-1</b> provides the voice conversation. Voice results
            cover the transcript captured when Evaluate was pressed, not a
            guaranteed complete spoken turn. Probabilities are not yet
            calibrated.
          </p>
          <button
            className="text-link"
            disabled={busy || !available}
            onClick={example}
          >
            Show a deliberate failure
          </button>
          {fixture && (
            <section
              className="failure-example"
              aria-label="Deliberate failure example"
            >
              <EvaluationSummary
                title="Deliberate failure example"
                rows={results[fixture.id]?.rows || []}
                assessed={results[fixture.id] ? 1 : 0}
                total={1}
              />
              <p className="small">
                An intentionally incorrect reply, assessed by the same checks.
                Excluded from your conversation results.
              </p>
              <EvidenceResponse
                record={fixture}
                evaluation={results[fixture.id]}
                error={errors[fixture.id]}
              />
            </section>
          )}
        </>
      )}
    </section>
  );
}
