const TRACKING = new Set(['fbclid', 'gclid', 'msclkid']);

export function normalizeUrl(input, opts = {}) {
  const url = new URL(input);
  url.hostname = url.hostname.toLowerCase();
  if ((url.protocol === 'https:' && url.port === '443') ||
      (url.protocol === 'http:' && url.port === '80')) {
    url.port = '';
  }
  const dropPrefixes = opts.dropPrefixes ?? ['utm_'];
  const params = [...url.searchParams.entries()]
    .filter(([k]) => !TRACKING.has(k) && !dropPrefixes.some((p) => k.startsWith(p)))
    .sort(([a], [b]) => a.localeCompare(b));
  url.search = '';
  for (const [k, v] of params) url.searchParams.append(k, v);
  if (url.pathname.length > 1 && url.pathname.endsWith('/')) {
    url.pathname = url.pathname.replace(/\/+$/, '');
  }
  return url.toString();
}

export default { normalizeUrl };
