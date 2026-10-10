# Argand

An independent senior-maths tutoring prototype, inspired by the clarity of Mathspace's learning interface. It uses its own name, icon and original questions, with no Mathspace logo or affiliation.

## Run locally

```sh
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
npm ci
npm run build
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 18770
```

Open http://127.0.0.1:18770. The server serves the built React app and API on the same origin. Rebuild the frontend after editing it. SQLite attempt records are local and gitignored.

## Try it

1. Explore the four-stage lesson: coordinates of 1 + i, its distance and angle, and squaring both roots of 2i, and a rotating-arrow example of AC voltage. Then select Try it yourself.
2. Submit `2` for `z³ = 8`. It is a valid but incomplete root set.
3. Submit `-1+i*sqrt(3)` and `-1-i*sqrt(3)` one at a time. The root set is checked, but prose reasoning is not certified.
4. Ask for hints or explicitly reveal the worked solution. The UI labels authored guidance honestly.
5. Press Evaluate below Chat to Argand at any time, including during voice. Evaluation also runs automatically when the final correct root is collected. Overall assertion counts precede expandable turn-by-turn results and a short model explanation; the deliberate failure example remains separate. The response incorrectly calls a partial set complete. The report quotes the immutable student, checker and tutor evidence.

One practice exercise is implemented: cube roots of 8. The lesson uses square roots of 2i, so it does not disclose the practice answers. Root entry supports exact integers, fractions, `i`, `sqrt(nonnegative integer)`, arithmetic and bounded integer powers. Unsupported notation and prose remain not checked. The parser never evaluates Python input.

## Evaluation services

Jev calls TypeSafe's typed API with pinned `jev-1.13.0` and applicable behavioural assertions as Noul probabilities of satisfaction. A tick means probability above 0.65; a cross means below 0.35; a dot means uncertain from 0.35 through 0.65 inclusive. These are model judgments, not proven facts. Inapplicable requirements are unscored. Every failed or uncertain (0.35–0.65) assertion gets a separate GPT-6.1-Sol review that may support or disagree with the flag; exact quotes are validated against the stored evidence. It requires `TYPESAFE_API_KEY` in the server environment, loaded through the canonical service loader. No keys belong in this repository. API errors do not become passes. The threshold has not been calibrated; no live evaluation is claimed until a response is recorded.

The investigator uses live OpenAI Responses with structured output. If unavailable or its quotes cannot be verified, the Jev result remains visible with an annotation error. The deliberate failure is authored and clearly separated from actual conversation records. Written feedback and voice reasoning both use `gpt-6.1-sol`; GPT-Live supplies Willow speech. Practice shares the lesson card layout: question and checked-root diagram above a compact answer bar. Feedback appears beside the answer area; Hint, Worked solution and Reset remain available. Questions use Chat to Argand below the card. Typed entry uses a local MathLive maths field with a small symbol keypad. Students check one root at a time; the server stores one canonical collection shared with the graph, preserves it after incorrect or unsupported entries, and deduplicates equivalent roots. My working is a collapsible, unverified note shared with the tutor. The backend also supports typed chat via the Responses API. GPT-Live voice uses WebRTC and the GPT-6.1-Sol reasoning backend. Use Chat to Argand beneath the lesson or practice; microphone permission is required. An expandable Transcript shows your words, tutor responses and maths-check results. The small stop square closes the session. Willow is the fixed tutor voice. Disconnects display the reported reason. Voice receives lesson changes and checked answer context; timestamped transcript fragments, UI snapshots and tool evidence are saved when Evaluate is pressed or the voice connection closes and can be assessed in the inline evidence panel. These are client-observed excerpts, not guaranteed complete turns or verified audio. Voice-check tool arguments are rechecked with SymPy before evaluation. Evidence remains in SQLite; the visible conversation list spans lesson/practice navigation in the current page session, and resets on a page reload. The reasoning backend can call check_roots, routed through /api/voice/check to the restricted SymPy checker for either lesson or practice. Results return as tool evidence; they do not submit a practice attempt. The tutor can operate the lesson controls through the tools described below; it does not submit spoken equations. Typed answers still use SymPy; generated explanations are not symbolically verified.

Load credentials with `source ~/the-lab/bin/load-secrets.sh openai` and restart the backend. API keys stay server-side. Model access and live audio must be tested with a configured project key. Voice integration follows the [GPT-Live WebRTC guide](https://developers.openai.com/api/docs/guides/voice-webrtc?api=live).

## Verify

```sh
npm run build
.venv/bin/python -m pytest -q
```

Current limits: no verified live voice trial yet, prose proof checking, handwriting, school accounts, teacher-reviewed curriculum certification, twelve-problem corpus or full model/harness comparison. This local prototype is for adult review, not deployment to students. No real learning gains have been measured.

Source references: [QCAA Specialist Mathematics syllabus](https://www.qcaa.qld.edu.au/downloads/senior-qce/syllabuses/snr_maths_specialist_25_syll.pdf), [TypeSafe API](https://docs.typesafe.ai/api), [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice).


## Shared lesson state and diagram tools

The lesson controls and diagrams use one revisioned state in `src/lessonState.ts`. After changes settle for 200 ms, the same snapshot is sent to GPT-Live with `session.thinking.append` and to its reasoning backend with `response.item.create`. This debounce combines rapid slider movement; tools always read the current state immediately. Snapshot delivery does not guarantee a model has finished processing it.

`read_lesson_state` returns the current slide, explanation, controls and graph values (or current practice). `update_diagram` operates the same controls as the learner: coordinates, modulus/angle, root selection/squaring, wave phase and time. It requires the current revision; stale edits and controls not present on the current slide are rejected. Navigation remains learner-controlled. Tool results publish the resulting state to both models before reasoning continues.

With the local server running and Python Playwright installed, run `python scripts/verify_lesson_tools.py`. It uses a simulated voice transport to exercise tool messages through the real UI, including stale edits, all interactive slides, practice transitions and equality of the state sent to both models. It makes no OpenAI call.

## Visual practice
Practice has modulus (0–3) and angle (0–360°, step 5°) sliders. The cubed point moves immediately with the sliders on a second, separately labelled scale. After the slider settles, the server computes the exact polar value with SymPy and automatically collects an exact match. Approximate coordinate labels do not determine correctness. Added roots use the same recorded-attempt flow as typed roots. Equivalent 0°/360° candidates are deduplicated. No undiscovered roots or snapping guides are shown. The voice and reasoning models share the current candidate, cubed result and verification state; practice controls remain learner-operated.

Run `python scripts/verify_practice_explorer.py` against the local preview to check incorrect candidates, discovery of all roots, duplicates, reset, typed entry and laptop/mobile layout. These checks use the actual UI and local SymPy endpoint, without model calls.

Answer checks and automatically collected roots now request concise OpenAI feedback using the exact SymPy result and prior attempts. Generated feedback is recorded as T1 for Jev, alongside the immutable checker evidence C1. If generation fails, the attempt is still saved with explicitly labelled checker-only feedback. Both voice and reasoning contexts include the latest feedback; no microphone or voice session starts automatically.

MathLive fonts are bundled locally by Vite. Run `python scripts/verify_root_entry.py` for the mixed typed/visual journey, keypad, notes and viewport checks. This uses the configured live tutor.
