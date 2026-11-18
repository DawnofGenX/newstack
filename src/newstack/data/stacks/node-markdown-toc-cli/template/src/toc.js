export function parseHeadings(text) {
  const lines = text.split(/\r?\n/);
  const headings = [];
  let inFence = false;
  let fenceMarker = null;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fenceMatch = line.match(/^(```|~~~)/);
    if (fenceMatch) {
      if (!inFence) {
        inFence = true;
        fenceMarker = fenceMatch[1];
      } else if (line.startsWith(fenceMarker)) {
        inFence = false;
        fenceMarker = null;
      }
      continue;
    }
    if (inFence) continue;

    const atx = line.match(/^(#{1,6})\s+(.+?)\s*#*\s*$/);
    if (atx) {
      headings.push({ level: atx[1].length, text: atx[2].trim() });
      continue;
    }
    if (i + 1 < lines.length) {
      const next = lines[i + 1];
      if (/^=+\s*$/.test(next) && line.trim() !== '') {
        headings.push({ level: 1, text: line.trim() });
        i++;
        continue;
      }
      if (/^-{3,}\s*$/.test(next) && line.trim() !== '' && !/^-{3,}$/.test(line.trim())) {
        headings.push({ level: 2, text: line.trim() });
        i++;
        continue;
      }
    }
  }
  return headings;
}

export function slugify(text) {
  return text.trim().toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}

export function assignSlugs(headings) {
  const seen = new Map();
  return headings.map((h) => {
    const base = slugify(h.text) || 'section';
    const count = seen.get(base) || 0;
    seen.set(base, count + 1);
    const slug = count === 0 ? base : `${base}-${count}`;
    return { ...h, slug };
  });
}

export function renderToc(headings) {
  const slugged = assignSlugs(headings);
  const lines = [];
  for (const h of slugged) {
    const indent = '  '.repeat(Math.max(0, h.level - 1));
    lines.push(`${indent}- [${h.text}](#${h.slug})`);
  }
  return lines.join('\n');
}
