type VoiceEvent = Record<string, unknown>;

// Streaming tokens repeat the entire lesson snapshot. Keep one context per
// contiguous excerpt, retaining each fragment's text and timestamp offsets.
export function compactVoiceEvidence(events: VoiceEvent[]): VoiceEvent[] {
  const compact: VoiceEvent[] = [];
  for (const event of events) {
    if (
      (event.who !== "You" && event.who !== "Tutor") ||
      typeof event.text !== "string"
    ) {
      compact.push({ ...event });
      continue;
    }
    const previous = compact.at(-1);
    const fragment = {
      text: event.text,
      start_ms: event.start_ms,
      end_ms: event.end_ms,
    };
    if (
      previous?.who === event.who &&
      JSON.stringify(previous.context) === JSON.stringify(event.context)
    ) {
      previous.text = String(previous.text) + event.text;
      previous.end_ms = event.end_ms;
      (previous.fragments as VoiceEvent[]).push(fragment);
    } else {
      compact.push({ ...event, fragments: [fragment] });
    }
  }
  return compact;
}
