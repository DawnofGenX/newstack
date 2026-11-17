// SSE framing. A frame is a few `field: value` lines and a blank line.
//
// The two rules that bite people:
//   * `data:` may not contain a raw newline. The payload is JSON-encoded, so a
//     multi-line string becomes `\n` inside the JSON and the frame stays one
//     event. Writing `String(data)` instead splits it into two events.
//   * the event *name* is also a header. A topic containing a newline would
//     smuggle a whole extra frame into the stream, so topics are validated.

export const TOPIC_RE = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export function assertTopic(topic) {
  if (typeof topic !== "string" || !TOPIC_RE.test(topic)) {
    throw new RangeError(
      `topic must match ${TOPIC_RE} (letters, digits, dot, dash, underscore), got ${JSON.stringify(topic)}`,
    );
  }
  return topic;
}

/// One event as the wire sees it. `id:` is what the browser echoes back in
/// `Last-Event-ID` after a reconnect.
export function frame(event) {
  assertTopic(event.topic);
  const data = JSON.stringify(event.data ?? null);
  return `id: ${event.id}\nevent: ${event.topic}\ndata: ${data}\n\n`;
}

// A comment line. Proxies and load balancers drop an idle connection, and an
// SSE client that sees nothing for long enough considers the stream dead; a
// heartbeat keeps both happy without inventing events.
export const HEARTBEAT = ": ping\n\n";
