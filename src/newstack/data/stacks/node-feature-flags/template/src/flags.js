import crypto from 'node:crypto';

export const FLAGS = [
  { name: 'new-ui', percentage: 50 },
  { name: 'beta-search', percentage: 25 },
  { name: 'dark-mode', percentage: 100 },
];

export function bucket(flagName, userId) {
  const h = crypto.createHash('sha256').update(`${flagName}:${userId}`).digest();
  const n = h.readUInt32BE(0);
  return n % 100;
}

export function isEnabled(flag, userId) {
  if (!flag.enabled && flag.enabled !== undefined) {
    // support optional enabled flag
    if (flag.enabled === false) return false;
  }
  const threshold = Math.max(0, Math.min(100, flag.percentage ?? 0));
  return bucket(flag.name, userId) < threshold;
}

export function resolveFlags(flags, userId) {
  const out = {};
  for (const f of flags) {
    out[f.name] = isEnabled(f, userId);
  }
  return out;
}
