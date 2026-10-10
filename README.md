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

1. Explore the three-stage lesson: coordinates of 1 + i, its distance and angle, and squaring both roots of 2i. Then select Try it yourself.
2. Submit `2` for `z³ = 8`. It is a valid but incomplete root set.
2. Submit `2,-1+i*sqrt(3),-1-i*sqrt(3)`. The root set is checked, but prose reasoning is not certified.
3. Ask for hints or explicitly reveal the worked solution. The UI labels authored guidance honestly.
4. Open Evidence lab, load a deliberate failure and inspect the mock investigation. The response incorrectly calls a partial set complete. The report quotes the immutable student, checker and tutor evidence.

One practice exercise is implemented: cube roots of 8. The lesson uses square roots of 2i, so it does not disclose the practice answers. Root entry supports exact integers, fractions, `i`, `sqrt(nonnegative integer)`, arithmetic and bounded integer powers. Unsupported notation and prose remain not checked. The parser never evaluates Python input.

## Evaluation services

Jev integration calls TypeSafe's typed API with pinned `jev-1.13.0`, eight independent behavioural assertions, four possible choices and a provisional 0.90 confidence threshold. It requires `TYPESAFE_API_KEY` in the server environment, loaded through the canonical service loader. No keys belong in this repository. API errors do not become passes. The threshold has not been calibrated; no live evaluation is claimed until a response is recorded.

The OpenAI investigator is intentionally mocked. The deliberate failure has an authored evidence statement; all other attempts return insufficient evidence rather than a fabricated diagnosis. The investigator makes no OpenAI call. Typed Ask for help uses the Responses API when OPENAI_API_KEY is configured. GPT-Live voice uses WebRTC and a separate reasoning backend (default gpt-6-luna, configurable through OPENAI_REASONING_MODEL). Use the small microphone beneath the lesson (tooltip: Talk it through); microphone permission is required. A compact panel shows your words, tutor responses and maths-check results. End voice closes the session. Voice receives lesson changes and checked answer context; its transcript is shown locally but is not yet persisted or evaluated by Jev. The reasoning backend can call check_roots, routed through /api/voice/check to the restricted SymPy checker for either lesson or practice. Results return as tool evidence; they do not submit a practice attempt. The tutor does not operate lesson controls or submit spoken equations. Typed answers still use SymPy; generated explanations are not symbolically verified.

Load credentials with `source ~/the-lab/bin/load-secrets.sh openai` and restart the backend. API keys stay server-side. Model access and live audio must be tested with a configured project key. Voice integration follows the [GPT-Live WebRTC guide](https://developers.openai.com/api/docs/guides/voice-webrtc?api=live).

## Verify

```sh
npm run build
.venv/bin/python -m pytest -q
```

Current limits: no verified live voice trial yet, prose proof checking, handwriting, school accounts, teacher-reviewed curriculum certification, twelve-problem corpus or full model/harness comparison. This local prototype is for adult review, not deployment to students. No real learning gains have been measured.

Source references: [QCAA Specialist Mathematics syllabus](https://www.qcaa.qld.edu.au/downloads/senior-qce/syllabuses/snr_maths_specialist_25_syll.pdf), [TypeSafe API](https://docs.typesafe.ai/api), [TypeSafe Choice](https://docs.typesafe.ai/primitives/choice).
