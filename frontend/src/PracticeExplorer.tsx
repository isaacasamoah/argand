import { useEffect, useRef, useState, type ReactNode } from "react";
import { polarPoint } from "./lessonState";
type Result = {
  matches: boolean;
  exact: string | null;
  point: number[];
  cubed: number[];
};
export function PracticeExplorer({
  children,
  onAdd,
  onState,
  busy,
  roots,
  points,
}: {
  children: ReactNode;
  onAdd: (text: string) => Promise<boolean>;
  onState: (state: unknown) => void;
  busy: boolean;
  roots: string[];
  points: number[][];
}) {
  const [modulus, setModulus] = useState(1),
    [angle, setAngle] = useState(45),
    [result, setResult] = useState<Result | null>(null),
    [error, setError] = useState("");
  const rootsRef = useRef(roots),
    addRef = useRef(onAdd);
  addRef.current = onAdd;
  rootsRef.current = roots;
  const candidate = polarPoint(modulus, angle),
    cubed = polarPoint(modulus ** 3, angle * 3),
    cubeExtent = Math.max(10, Math.ceil(modulus ** 3 / 10) * 10);
  useEffect(() => {
    onState({
      controls: { modulus, angle },
      candidate,
      cubed,
      axes: { candidateExtent: 3, cubedExtent: cubeExtent },
      checker: result
        ? { source: "SymPy exact checker", matches: result.matches }
        : null,
      collectedRoots: roots,
    });
  }, [modulus, angle, result, roots]);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const response = await fetch("/api/practice/cube", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ modulus, angle }),
          signal: controller.signal,
        });
        if (!response.ok)
          throw new Error(
            "Could not verify this point. Move a slider to retry.",
          );
        const checked: Result = await response.json();
        if (controller.signal.aborted) return;
        setResult(checked);
        if (
          checked.matches &&
          checked.exact &&
          !rootsRef.current.includes(checked.exact)
        ) {
          await addRef.current(checked.exact);
        }
      } catch (e) {
        if (!controller.signal.aborted) setError((e as Error).message);
      }
    }, 200);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [modulus, angle]);
  function move(r: number, a: number) {
    setModulus(r);
    setAngle(a);
    setResult(null);
    setError("");
  }
  function plane(
    label: string,
    extent: number,
    point: number[] | null,
    target?: number[],
  ) {
    const scale = 66 / extent,
      tick = extent === 3 ? 1 : extent / 2,
      ticks = Array.from({ length: extent === 3 ? 6 : 4 }, (_, i) =>
        i < (extent === 3 ? 3 : 2)
          ? -extent + i * tick
          : (i - (extent === 3 ? 3 : 2) + 1) * tick,
      );
    return (
      <svg viewBox="0 0 180 180" role="img" aria-label={label}>
        <path d="M12 90H168 M90 12V168" stroke="#a3b5bd" />
        {ticks.map((n) => (
          <g key={n}>
            <path
              d={`M${90 + n * scale} 87v6 M87 ${90 - n * scale}h6`}
              stroke="#a3b5bd"
            />
            <text x={90 + n * scale} y="105" textAnchor="middle">
              {n}
            </text>
            <text x="84" y={94 - n * scale} textAnchor="end">
              {n}
            </text>
          </g>
        ))}
        <text x="165" y="82">
          Re
        </text>
        <text x="97" y="16">
          Im
        </text>
        {!target &&
          points.map(([x, y], i) => (
            <circle
              key={i}
              cx={90 + x * scale}
              cy={90 - y * scale}
              r="4"
              fill="#157e79"
            />
          ))}
        {target && (
          <>
            <circle
              cx={90 + target[0] * scale}
              cy={90 - target[1] * scale}
              r="7"
              fill="none"
              stroke="#c08628"
              strokeWidth="2"
            />
            <text x={90 + target[0] * scale} y="119" textAnchor="middle">
              target 8
            </text>
          </>
        )}
        {point && (
          <>
            <path
              d={`M90 90L${90 + point[0] * scale} ${90 - point[1] * scale}`}
              stroke="#078d85"
              strokeWidth="2"
            />
            <circle
              cx={90 + point[0] * scale}
              cy={90 - point[1] * scale}
              r="4"
              fill="#078d85"
            />
          </>
        )}
      </svg>
    );
  }
  return (
    <>
      <div className="practice-question">
        {children}
        <div className="sliders practice-sliders">
          <label>
            Modulus: {modulus.toFixed(1)}
            <input
              aria-label="Candidate modulus"
              type="range"
              min="0"
              max="3"
              step=".1"
              value={modulus}
              disabled={busy}
              onChange={(e) => move(Number(e.target.value), angle)}
            />
          </label>
          <label>
            Angle: {angle}°
            <input
              aria-label="Candidate angle"
              type="range"
              min="0"
              max="360"
              step="5"
              value={angle}
              disabled={busy}
              onChange={(e) => move(modulus, Number(e.target.value))}
            />
          </label>
        </div>
      </div>
      <div className="practice-explorer">
        <div className="explorer-planes">
          <div>
            <b>Your point · z</b>
            {plane("Candidate point", 3, candidate)}
            <small>
              ≈ ({candidate[0].toFixed(2)}, {candidate[1].toFixed(2)})
            </small>
          </div>
          <div>
            <b>After cubing · z³</b>
            {plane("Cubed point and target", cubeExtent, cubed, [8, 0])}
            <small>{`≈ (${cubed[0].toFixed(2)}, ${cubed[1].toFixed(2)})`}</small>
          </div>
        </div>
        <p className="explorer-result" role="status">
          {error ||
            (result?.matches
              ? roots.includes(result.exact || "")
                ? "Root collected"
                : "Collecting root…"
              : "Move the sliders to make z³ reach 8.")}
          {roots.length > 0 && (
            <span className="collected-roots">
              {" "}
              · {roots.length} / 3 found:{" "}
              {roots
                .map((root) =>
                  root.replaceAll("sqrt(3)", "√3").replaceAll("*", ""),
                )
                .join("; ")}
            </span>
          )}
        </p>
      </div>
    </>
  );
}
