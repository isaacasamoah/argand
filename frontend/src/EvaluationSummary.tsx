import type { Row } from "./evidence";
import { counts } from "./evidence";
export function EvaluationSummary({
  title,
  rows,
  assessed,
  total,
}: {
  title: string;
  rows: Row[];
  assessed: number;
  total: number;
}) {
  const totals = counts(rows);
  return (
    <div className="evaluation-overall" role="status">
      <h3>{title}</h3>
      <p>
        ✓ {totals.pass} passed · ✗ {totals.fail} failed · • {totals.uncertain}{" "}
        uncertain
      </p>
      <small>
        {assessed} of {total} recorded replies assessed · counts are assertion
        checks
      </small>
    </div>
  );
}
