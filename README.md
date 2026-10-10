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
2. Submit `2,-1+i*sqrt(3),-1-i*sqrt(3)`. The root set is checked, but prose reasoning is not certified.
3. Ask for hints or explicitly reveal the worked solution. The UI labels authored guidance honestly.
4. Open Evidence lab, load a deliberate failure and inspect the mock investigation. The response incorrectly calls a partial set complete. The report quotes the immutable student, checker and tutor evidence.

One practice exercise is implemented: cube roots of 8. The lesson uses square roots of 2i, so it does not disclose the practice answers. Root entry supports exact integers, fractions, `i`, `sqrt(nonnegative integer)`, arithmetic and bounded integer powers. Unsupported notation and prose remain not checked. The parser never evaluates Python input.

## Evaluation services

Jev integration calls TypeSafe's typed API with pinned `jev-1.13.0`, eight independent behavioural assertions, four possible choices and a provisional 0.90 confidence threshold. It requires `TYPESAFE_API_KEY` in the server environment, loaded through the canonical service loader. No keys belong in this repository. API errors do not become passes. The threshold has not been calibrated; no live evaluation is claimed until a response is recorded.

The OpenAI investigator is intentionally mocked. The deliberate failure has an authored evidence statement; all other attempts return insufficient evidence rather than a fabricated diagnosis. The investigator makes no OpenAI call. Practice shares the lesson card layout: question and checked-root diagram above a compact answer bar. Feedback appears beside the answer area; Hint, Worked solution and Reset remain available. Questions use Chat to Argand below the card. The backend also supports typed chat via the Responses API. GPT-Live voice uses WebRTC and a separate reasoning backend (default gpt-6-luna, configurable through OPENAI_REASONING_MODEL). Use Chat to Argand beneath the lesson or practice; microphone permission is required. An expandable Transcript shows your words, tutor responses and maths-check results. The small stop square closes the session. Willow is the fixed tutor voice. Disconnects display the reported reason. Voice receives lesson changes and checked answer context; its transcript is shown locally but is not yet persisted or evaluated by Jev. The reasoning backend can call check_roots, routed through /api/voice/check to the restricted SymPy checker for either lesson or practice. Results return as tool evidence; they do not submit a practice attempt. The tutor can operate the lesson controls through the tools described below; it does not submit spoken equations. Typed answers still use SymPy; generated explanations are not symbolically verified.

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

`read_lesson_state` returns the current slide, explanation, controls and graph values (or current practice). `update_diagram` operates the same controls as the learner: coordinates, root selection/squaring, wave phase and time. It requires the current revision; stale edits and controls not present on the current slide are rejected. Navigation remains learner-controlled. Tool results publish the resulting state to both models before reasoning continues.

With the local server running and Python Playwright installed, run `python scripts/verify_lesson_tools.py`. It uses a simulated voice transport to exercise tool messages through the real UI, including stale edits, all interactive slides, practice transitions and equality of the state sent to both models. It makes no OpenAI call.
