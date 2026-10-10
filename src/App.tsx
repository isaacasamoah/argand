import { api } from "./api";
import { EvidencePanel } from "./EvidencePanel";
import { mergeRecords, type EvidenceRecord } from "./evidence";
import { RootEntry } from "./RootEntry";
import { PracticeExplorer } from "./PracticeExplorer";
import { useLessonState, lessonSnapshot } from "./lessonState";
import { VoiceTutor, type VoiceHandle } from "./VoiceTutor";
import { Lesson } from "./Lesson";
import React, { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowLeft,
  BookOpen,
  ChevronRight,
  Compass,
  X,
  AlertCircle,
} from "lucide-react";
import katex from "katex";
import "katex/dist/katex.min.css";
import "./style.css";
type Problem = {
  id: string;
  title: string;
  n: number;
  value: number;
  latex: string;
  level: string;
};
type Config = {
  problems: Problem[];
  assertions: Assertion[];
  jev_available: boolean;
  tutor_available: boolean;
};
type Assertion = { id: string; title: string; requirement: string };
type Attempt = {
  id: string;
  student: string;
  tutor: string;
  tutor_source: string;
  action: string;
  collected_roots: string[];
  collection_points: number[][];
  checker: {
    status: string;
    detail: string;
    points: number[][];
    valid: boolean[];
  };
  versions: Record<string, string>;
  evidence: Record<string, string>;
};
function MathText({
  value,
  block = false,
}: {
  value: string;
  block?: boolean;
}) {
  return (
    <span
      dangerouslySetInnerHTML={{
        __html: katex.renderToString(value, {
          throwOnError: false,
          displayMode: block,
        }),
      }}
    />
  );
}
const EMPTY_ROOTS: string[] = [];
export function App() {
  const [config, setConfig] = useState<Config>();
  const [pi, setPi] = useState(0);
  const [exploration, setExploration] = useState<unknown>(null);
  const [practiceKey, setPracticeKey] = useState(0);
  const [lesson, setLesson] = useState(true);
  useLessonState();
  const [records, setRecords] = useState<EvidenceRecord[]>([]);
  const [evidenceOpen, setEvidenceOpen] = useState(false);
  const [autoEvaluate, setAutoEvaluate] = useState(0);
  const voice = React.useRef<VoiceHandle>(null);
  const [working, setWorking] = useState("");
  const submissionPending = React.useRef(false);
  const [attempts, setAttempts] = useState<Attempt[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [hint, setHint] = useState(0);
  useEffect(() => {
    api<Config>("config")
      .then(setConfig)
      .catch((e) => setError(e.message));
  }, []);
  const p = config?.problems[pi],
    last = attempts.at(-1),
    collected = last?.collected_roots || EMPTY_ROOTS;
  async function act(action: string, answer = "") {
    if (!p || submissionPending.current) return false;
    submissionPending.current = true;
    setBusy(true);
    setError("");
    try {
      const a = await api<Attempt>("attempts", {
        problem_id: p.id,
        text: answer,
        action,
        hint_level: Math.min(hint, 2),
        parent_id: last?.id,
      });
      setAttempts((previous) => [...previous.slice(-19), a]);
      setRecords((previous) => mergeRecords(previous, [a]));
      if (
        a.checker.status === "complete" &&
        last?.checker.status !== "complete" &&
        action === "collect"
      )
        setAutoEvaluate((n) => n + 1);
      if (action === "hint") setHint((x) => x + 1);
      return (
        action !== "collect" ||
        ["incomplete", "complete"].includes(a.checker.status)
      );
    } catch (e) {
      setError((e as Error).message);
      return false;
    } finally {
      submissionPending.current = false;
      setBusy(false);
    }
  }
  function change(i: number) {
    setPracticeKey((k) => k + 1);
    setExploration(null);
    setPi(i);
    setAttempts([]);
    setWorking("");
    setHint(0);
    setError("");
  }
  return (
    <>
      <header>
        <a className="brand" href="/" aria-label="Argand home">
          <span className="brandmark">
            <Compass size={23} />
          </span>
          argand<span className="prototype">LAB</span>
        </a>
        <div className="avatar">IA</div>
      </header>
      <div className="shell lesson-shell">
        <aside>
          <div className="course-icon">
            <BookOpen size={24} />
          </div>
          <p className="eyebrow">YOUR COURSE</p>
          <h3>
            Specialist
            <br />
            Mathematics
          </h3>
          <p className="subtle">Senior secondary · Queensland</p>
          <hr />
          <div className="unit-label">
            UNIT 3 <span>01</span>
          </div>
          <h4>Complex numbers</h4>
          <div className="lessons">
            <button
              className={lesson ? "chosen" : ""}
              onClick={() => {
                setLesson(true);
              }}
            >
              <span className="lesson-number">1</span>
              <span>
                The lesson<small>See how complex roots work</small>
              </span>
            </button>
            <button
              className={!lesson ? "chosen" : ""}
              onClick={() => {
                setLesson(false);
              }}
            >
              <span className="lesson-number">2</span>
              <span>
                Your practice<small>Find the missing roots</small>
              </span>
            </button>
          </div>
        </aside>
        <main>
          <div className="breadcrumb">
            Specialist Mathematics <ChevronRight size={13} /> Complex numbers{" "}
            <ChevronRight size={13} /> {lesson ? "Lesson" : "Practice"}
          </div>
          {error && (
            <div role="alert" className="error">
              <AlertCircle size={18} />
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {!p ? (
            <p>Loading your workspace…</p>
          ) : lesson ? (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">SEE IT BEFORE YOU SOLVE IT</p>
                  <h1>Complex numbers and their roots</h1>
                  <p className="subtle">
                    A short exploration of complex numbers and their roots.
                  </p>
                </div>
              </div>
              <Lesson
                onPractice={() => {
                  change(0);
                  setLesson(false);
                }}
              />
            </>
          ) : (
            <>
              <section className="lesson-card practice-card">
                <div className="lesson-intro">
                  <span className="pill">Your practice</span>
                  <button className="text-link" onClick={() => setLesson(true)}>
                    Revisit the lesson <ArrowLeft size={15} />
                  </button>
                </div>
                <div className="lesson-layout">
                  <PracticeExplorer
                    key={practiceKey}
                    onAdd={(answer) => act("collect", answer)}
                    roots={collected}
                    points={last?.collection_points || []}
                    onState={setExploration}
                    busy={busy}
                  >
                    <h2>Find every complex root of</h2>
                    <div className="equation">
                      <MathText value={p.latex} block />
                    </div>
                    <p>
                      Express your answers in Cartesian form, a + bi. Explain
                      why there are no other distinct roots.
                    </p>
                  </PracticeExplorer>
                </div>
                {last && (
                  <div className="practice-feedback" role="status">
                    <p>{last.tutor}</p>
                    <button
                      className="trace-link"
                      onClick={() => setEvidenceOpen(true)}
                    >
                      View evidence <ArrowRight size={12} />
                    </button>
                  </div>
                )}
                <RootEntry
                  key={practiceKey}
                  busy={busy}
                  onCheck={(value) => act("collect", value)}
                >
                  <button
                    className="text-link"
                    type="button"
                    disabled={busy}
                    onClick={() => act("hint")}
                  >
                    {hint === 0 ? "Hint" : "Another hint"}
                  </button>
                  <button
                    className="text-link"
                    type="button"
                    disabled={busy}
                    onClick={() => act("solution")}
                  >
                    Worked solution
                  </button>
                  <button
                    className="text-link"
                    type="button"
                    disabled={busy}
                    onClick={() => change(pi)}
                  >
                    Reset
                  </button>
                </RootEntry>
                <details className="working-notes">
                  <summary>My working</summary>
                  <label htmlFor="working-notes">
                    Notes to discuss with Argand · not checked
                  </label>
                  <textarea
                    id="working-notes"
                    value={working}
                    maxLength={2000}
                    onChange={(e) => setWorking(e.target.value)}
                    placeholder="Jot down a step or a question. Paper is fine too."
                  />
                </details>
              </section>
            </>
          )}
          {p && (
            <VoiceTutor
              ref={voice}
              onEvidence={(items) =>
                setRecords((previous) => mergeRecords(previous, items))
              }
              key={p.id}
              available={!!config?.tutor_available}
              problemId={p.id}
              lesson={lesson}
              context={JSON.stringify(
                lesson
                  ? lessonSnapshot()
                  : {
                      mode: "practice",
                      problem: p.latex,
                      exploration,
                      working: { text: working, status: "not checked" },
                      collectedRoots: collected,
                      latestAttempt: last
                        ? {
                            student: last.student,
                            checker: last.checker,
                            feedback: last.tutor,
                          }
                        : null,
                    },
              )}
              parentId={last?.id}
            />
          )}
          <EvidencePanel
            capture={async () =>
              mergeRecords(records, (await voice.current?.capture()) || [])
            }
            autoEvaluate={autoEvaluate}
            records={records}
            open={evidenceOpen}
            onToggle={setEvidenceOpen}
            available={!!config?.jev_available}
          />
        </main>
      </div>
      {busy && (
        <div className="working-toast" role="status">
          <span className="spinner" />
          Working…
        </div>
      )}
    </>
  );
}
