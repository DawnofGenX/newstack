import { countText } from "./counts.js";

export const ERROR_CODES = {
  invalidJson: "invalid_json",
  unknownType: "unknown_type",
  invalidText: "invalid_text",
};

export function parseFrame(raw) {
  let message;
  try {
    message = JSON.parse(raw);
  } catch {
    return { ok: false, code: ERROR_CODES.invalidJson, detail: "the frame is not JSON" };
  }
  if (message === null || typeof message !== "object" || Array.isArray(message)) {
    return { ok: false, code: ERROR_CODES.invalidJson, detail: "a frame is a JSON object" };
  }
  if (typeof message.type !== "string") {
    return { ok: false, code: ERROR_CODES.unknownType, detail: "every frame names a type" };
  }
  return { ok: true, message };
}

export function statsReply(text) {
  const counts = countText(text);
  return { type: "stats", lines: counts.lines, words: counts.words, bytes: counts.bytes };
}

// A frame is either answered on the socket that sent it or broadcast to the room.
export function handleFrame(raw) {
  const parsed = parseFrame(raw);
  if (!parsed.ok) {
    return { kind: "error", frame: { type: "error", code: parsed.code, detail: parsed.detail } };
  }
  const message = parsed.message;
  if (message.type === "ping") {
    return { kind: "reply", frame: { type: "pong" } };
  }
  if (message.type === "stats") {
    if (typeof message.text !== "string") {
      return {
        kind: "error",
        frame: {
          type: "error",
          code: ERROR_CODES.invalidText,
          detail: "stats needs a text string",
        },
      };
    }
    return { kind: "reply", frame: statsReply(message.text) };
  }
  return {
    kind: "error",
    frame: {
      type: "error",
      code: ERROR_CODES.unknownType,
      detail: `no handler for ${JSON.stringify(message.type)}`,
    },
  };
}
