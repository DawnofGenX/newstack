export function parseDuration(input) {
  const s = String(input).trim();
  if (s === "") throw new Error("empty duration");
  const re = /(\d+(?:\.\d+)?)\s*(ms|s|m|h|d|w)/gi;
  let total = 0;
  let matched = "";
  let m;
  while ((m = re.exec(s)) !== null) {
    const val = parseFloat(m[1]);
    const unit = m[2].toLowerCase();
    const mult = { ms: 1, s: 1000, m: 60000, h: 3600000, d: 86400000, w: 604800000 }[unit];
    total += val * mult;
    matched += m[0];
  }
  if (matched.replace(/\s/g, "") !== s.replace(/\s/g, "")) throw new Error("invalid duration: " + input);
  return total;
}