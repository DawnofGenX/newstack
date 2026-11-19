export type Strength = { score: number; label: string; entropy: number };

const COMMON = ["password", "123456", "qwerty", "letmein", "admin", "welcome"];

export function scorePassword(pw: string): Strength {
  const s = pw ?? "";
  let score = 0;
  const hasLower = /[a-z]/.test(s);
  const hasUpper = /[A-Z]/.test(s);
  const hasDigit = /\d/.test(s);
  const hasSymbol = /[^A-Za-z0-9]/.test(s);
  const classes = [hasLower, hasUpper, hasDigit, hasSymbol].filter(Boolean).length;

  if (s.length >= 8) score++;
  if (s.length >= 12) score++;
  if (classes >= 3) score++;
  if (classes === 4) score++;

  // penalties
  const lower = s.toLowerCase();
  for (const c of COMMON) {
    if (lower.includes(c)) { score = Math.max(0, score - 2); break; }
  }
  if (/(.)\1{3,}/.test(s)) score = Math.max(0, score - 1);
  if (score > 4) score = 4;

  const labels = ["very weak", "weak", "fair", "strong", "very strong"];
  const entropy = Math.round(s.length * Math.log2(Math.max(classes, 1) * 10 + 1));
  return { score, label: labels[score], entropy };
}