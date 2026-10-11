import assert from "node:assert/strict";
import test from "node:test";
import { compactVoiceEvidence } from "../src/voiceEvidence.ts";

test("long streaming conversations fit without dropping text, context or timestamps", () => {
  const context = { mode: "lesson", explanation: "A".repeat(800) };
  const events = Array.from({ length: 2500 }, (_, i) => ({
    who: "Tutor",
    text: ` ${i}`,
    start_ms: i * 200,
    end_ms: (i + 1) * 200,
    context,
  }));
  const result = compactVoiceEvidence(events);
  assert.ok(JSON.stringify(events).length > 500000);
  assert.ok(JSON.stringify(result).length < 500000);
  assert.equal(result.length, 1);
  assert.equal(result[0].text, events.map((e) => e.text).join(""));
  assert.equal(result[0].fragments.length, events.length);
  assert.equal(result[0].start_ms, 0);
  assert.equal(result[0].end_ms, 500000);
  assert.deepEqual(result[0].context, context);
  assert.equal(events[0].text, " 0");
});
test("speaker, tool and context changes remain separate and ordered", () => {
  const events = [
    { who: "Tutor", text: "one", context: { revision: 1 } },
    { who: "You", text: "two", context: { revision: 1 } },
    { who: "Tutor", text: "three", context: { revision: 1 } },
    { who: "Tool", name: "update_diagram", result: { ok: true } },
    { who: "Tutor", text: "four", context: { revision: 1 } },
    { who: "Tutor", text: "five", context: { revision: 2 } },
  ];
  assert.equal(compactVoiceEvidence(events).length, 6);
  assert.deepEqual(compactVoiceEvidence(events)[3], events[3]);
});
