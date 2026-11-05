export function readTextMember(raw) {
  let value;
  try {
    value = JSON.parse(raw);
  } catch {
    return { kind: "invalid" };
  }
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return { kind: "invalid" };
  }
  if (!Object.prototype.hasOwnProperty.call(value, "text")) return { kind: "missing" };
  if (typeof value.text !== "string") return { kind: "invalid" };
  return { kind: "text", text: value.text };
}

export function queryText(search) {
  const raw = search.startsWith("?") ? search.slice(1) : search;
  let found = null;
  for (const pair of raw.split("&")) {
    if (!pair) continue;
    const at = pair.indexOf("=");
    const name = at === -1 ? pair : pair.slice(0, at);
    if (decodeURIComponent(name) !== "text") continue;
    found = at === -1 ? "" : decodeURIComponent(pair.slice(at + 1));
    break;
  }
  return found;
}
