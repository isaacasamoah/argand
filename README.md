# Argand

A small, working demo of a voice-enabled maths tutor with inspectable evaluations. Explore complex numbers on an interactive diagram, solve a related problem, and inspect how the tutor's replies were checked.

Built as an independent senior-secondary maths prototype. Inspired by the clarity of Mathspace's learning interface; no Mathspace logo or affiliation.

## Try the demo

1. Work through the four lesson stages: Cartesian coordinates, modulus and argument, square roots of `2i`, and an AC voltage example.
2. Select **Your practice** to find the cube roots of `8`. Explore with modulus/angle sliders or enter one root at a time with the maths keypad. Exact matches are collected automatically; the lesson does not reveal the practice answers.
3. Select **Chat to Argand** to discuss the current diagram. The tutor can adjust lesson controls, read the current state and call the maths checker. A small red square ends voice; the transcript is expandable.
4. Press **Evaluate** at any time, including during voice. Evaluation also runs when the final correct root is collected. Overall assertion counts appear above expandable reply-by-reply results.
5. Open **Show a deliberate failure** to compare an intentionally incorrect reply against the same checks. Its summary and evidence are separate from your conversation results.

The practice roots are `2`, `-1+i*sqrt(3)` and `-1-i*sqrt(3)`. Submit them separately. Collecting them verifies the values, not a written proof or a learning outcome.

## Run your own copy

The public source is **bring your own API keys**. Clone it with `git clone https://github.com/isaacasamoah/argand.git`, then `cd argand`. Access to the separately hosted review demo is by private invitation; no invitation or provider credential is included here.

## Run locally

Use Node.js 22+ and Python 3.11+ (verified locally with Python 3.13). The commands below use [uv](https://docs.astral.sh/uv/).

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r backend/requirements-dev.txt
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python -m uvicorn argand.server:app --app-dir backend --host 127.0.0.1 --port 18770
```

Open **http://127.0.0.1:18770**. FastAPI serves the built frontend and API from one origin. Rebuild after frontend edits, or run `npm --prefix frontend run dev` in another terminal to rebuild on changes. Restart the Python server after backend edits.

Supply provider credentials in the server's environment using your secret manager before starting it:

| Variable           | Purpose                                                                     |
| ------------------ | --------------------------------------------------------------------------- |
| `OPENAI_API_KEY`   | Written feedback, voice sessions and failure annotations                    |
| `TYPESAFE_API_KEY` | Jev assertion judgments                                                     |
| `ARGAND_DB`        | Optional SQLite path; defaults to `attempts.sqlite3` in the repository root |

Do not put keys in frontend code. Without keys, the lesson, diagrams and exact maths checks still work with explicitly authored feedback; voice and model evaluation are unavailable. Provider calls use the configured accounts and may incur charges. Voice requires microphone permission and access to the configured models.

## How the checks work

SymPy verifies mathematical values. The tutor receives that result and responds to the learner. Jev then judges the recorded reply against applicable teaching requirements; it is not asked to replace the symbolic maths checker.

| Component                            | Model or implementation    | Responsibility                                                |
| ------------------------------------ | -------------------------- | ------------------------------------------------------------- |
| Maths checker                        | Restricted parser + SymPy  | Exact arithmetic, root validity and collection completeness   |
| Tutor reasoning and written feedback | `gpt-6.1-sol`              | Coaching grounded in the current lesson and checker evidence  |
| Spoken conversation                  | `gpt-live-1`, Willow voice | Live speech with delegated reasoning and diagram tools        |
| Assertion evaluator                  | TypeSafe `jev-1.13.0`      | Noul probabilities that individual requirements are satisfied |
| Evidence annotations                 | `gpt-6.1-sol`              | Review failed/uncertain judgments and cite recorded evidence  |

Jev is TypeSafe's model for structured judgments. Each applicable requirement receives a probability of satisfaction: **✓ above 65%, • uncertain from 35% through 65%, ✗ below 35%**. These thresholds are prototype choices and are not calibrated. Inapplicable requirements are unscored. Summary counts describe assertion checks, not a percentage of successful students or conversations.

Failed and uncertain checks receive an OpenAI annotation. The annotation may support or disagree with Jev's judgment, or report insufficient evidence. Citation text must occur in the saved evidence; rejected citations and provider errors remain visible as errors, never passes. The deliberate failure example is authored, but its evaluation and annotations use the real providers.

## State and evidence

- Lesson diagrams share one revisioned state. GPT-Live and its reasoning model receive the same snapshots. Diagram tools reject stale revisions and controls absent from the current slide.
- `read_lesson_state` reads the visible state; `update_diagram` changes lesson controls; `check_roots` invokes the restricted checker. Navigation and practice sliders remain learner-controlled.
- Typed roots and slider discoveries share one server-owned collection. Invalid input preserves correct work; equivalent roots are deduplicated. Exact arithmetic determines matches, not rounded graph labels.
- **My working** is an optional, unverified note shared with the tutor. Unsupported maths and prose remain unverified.
- SQLite stores immutable answer records, voice snapshots and evaluations. Voice evidence includes transcript fragments, UI context and tool observations; checker arguments are rechecked with SymPy. Snapshots can be evaluated while speaking, and later snapshots replace earlier versions in the visible results without double-counting them.
- Voice excerpts are client-observed transcripts, not guaranteed complete turns or verified audio. The visible conversation list survives lesson/practice navigation but resets on a page reload; saved records remain in SQLite.

Keys stay server-side. Evaluations send recorded replies and context to TypeSafe and OpenAI. Treat the local database as conversation data; it is excluded from Git along with environment files and SQLite journal files. This demo has no accounts or public-server authentication: keep it bound to loopback.

## Code map

```text
frontend/
  src/                      React components, diagrams, voice and evaluation UI
  index.html                Browser entry point
  package.json              Frontend dependencies and build commands
  vite.config.ts            Bundling and local maths fonts
backend/
  argand/
    server.py               FastAPI routes and tutor/voice orchestration
    math_checks.py          Restricted parser and exact SymPy checks
    curriculum.py           Exercise and explicitly authored guidance
    models.py               Shared reasoning model identifier
    evaluation.py           Assertions, Jev judgments and annotations
    storage.py              SQLite records
    review_access.py        Optional expiring review invitation gate
  tests/                    Isolated Python unit and API tests
  pyproject.toml            Python lint and test configuration
  requirements*.txt         Runtime and development dependencies
tests/browser/              Browser journeys covering frontend and backend
tools/                      Hosting and maintenance helpers
```

MathLive fonts are bundled locally. There is no browser-side provider key or external font dependency.

## Verification and formatting

```sh
npm --prefix frontend run build
npm --prefix frontend run format:check
.venv/bin/python -m pytest -c backend/pyproject.toml backend/tests -q
.venv/bin/ruff check --config backend/pyproject.toml .
.venv/bin/ruff format --config backend/pyproject.toml --check .
```

Use `npm --prefix frontend run format` and `.venv/bin/ruff format --config backend/pyproject.toml .` to apply formatting. The TypeScript build rejects unused locals and parameters. Unit tests use isolated temporary databases and provider doubles; they do not call paid services.

For browser verification, install Playwright separately and start the local server:

```sh
uv pip install --python .venv/bin/python playwright
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser/verify_inline_evidence.py
```

The inline-evidence test simulates voice transport, evaluator responses and completed-answer delivery while exercising the real UI and evidence storage. It covers evaluation during voice, snapshot replacement, automatic evaluation, uncertainty display and mobile width. Other scripts (`verify_lesson_tools.py`, `verify_practice_explorer.py`, `verify_root_entry.py`) exercise the local UI and checker; with provider credentials configured, answer submission also makes live tutor calls. They are not offline tests. Screenshots go to the system temporary directory under `argand-evidence`, or `ARGAND_EVIDENCE_DIR` when set.

## Scope

One lesson sequence and one practice problem are implemented. There is no handwriting recognition, verified prose-proof assessment, account system, school deployment or measured learning improvement. Evaluation reliability and curriculum suitability need further review. Live provider behaviour depends on account access and model availability; automated browser simulations do not prove microphone/audio quality.

References: [QCAA Specialist Mathematics syllabus](https://www.qcaa.qld.edu.au/downloads/senior-qce/syllabuses/snr_maths_specialist_25_syll.pdf), [TypeSafe Noul](https://docs.typesafe.ai/primitives/noul), [OpenAI GPT-Live](https://developers.openai.com/api/docs/guides/live).

## Optional private review hosting

The same app can run behind an HTTPS reverse proxy such as Tailscale Funnel. Set all three variables in the hosting environment: `ARGAND_PUBLIC_ORIGIN` (exact HTTPS origin), `ARGAND_REVIEW_TOKEN` (a random secret of at least 32 characters), and `ARGAND_REVIEW_EXPIRES` (expiry as Unix seconds). Use a separate `ARGAND_DB` for reviewer records.

The invitation URL carries the token in a fragment, which is removed from the browser address before login. Login sets a Secure, HttpOnly, SameSite cookie. The hosted gate rejects expired invitations, unexpected hosts/origins and requests without access. Possession of an invitation grants access; this is not email identity verification. Keep invitation links out of Git and share them only with intended reviewers. `tools/review_invite.py` lets the hosting owner open or copy an invitation locally after loading these environment variables.

Provider credit and billing limits remain provider-controlled. This app does not implement a monetary spending cap. Disable auto-renewal and configure the hosting accounts accordingly; provider exhaustion is reported by the model APIs. Public clones use the clone owner's accounts.

Normal local runs leave the review variables unset. The invitation gate is then disabled and the server should stay on loopback. The hosted machine must remain online for a Funnel link to work.
