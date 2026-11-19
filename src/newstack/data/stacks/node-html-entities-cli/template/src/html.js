// Pure HTML entity encode/decode helpers. No dependencies.

const NAMED = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

const REVERSE = Object.fromEntries(
  Object.entries(NAMED).map(([k, v]) => [v, k])
);

export function encodeEntities(input) {
  return String(input).replace(/[&<>"']/g, (ch) => NAMED[ch]);
}

export function decodeEntities(input) {
  const s = String(input);
  // numeric decimal/hex
  let out = s.replace(/&#x([0-9a-fA-F]+);?/g, (_, hex) =>
    String.fromCodePoint(parseInt(hex, 16))
  );
  out = out.replace(/&#(\d+);?/g, (_, dec) =>
    String.fromCodePoint(parseInt(dec, 10))
  );
  // named
  out = out.replace(/&(amp|lt|gt|quot|#39|apos);/g, (m) => {
    if (m === "&amp;") return "&";
    if (m === "&lt;") return "<";
    if (m === "&gt;") return ">";
    if (m === "&quot;") return '"';
    if (m === "&#39;" || m === "&apos;") return "'";
    return m;
  });
  return out;
}