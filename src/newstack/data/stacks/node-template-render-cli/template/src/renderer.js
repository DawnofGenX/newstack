const ESCAPE = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ESCAPE[ch]);
}

export function lookup(context, path) {
  if (context == null) return undefined;
  if (path === ".") return context;
  const parts = String(path).split(".");
  let cur = context;
  for (const p of parts) {
    if (cur == null || typeof cur !== "object") return undefined;
    cur = cur[p];
  }
  return cur;
}

function findSection(str, start) {
  let depth = 1;
  const re = /\{\{(.+?)\}\}/g;
  re.lastIndex = start;
  let m;
  while ((m = re.exec(str)) !== null) {
    const tag = m[1].trim();
    if (tag.startsWith("#") || tag.startsWith("^")) {
      depth += 1;
    } else if (tag.startsWith("/")) {
      depth -= 1;
      if (depth === 0) {
        return { body: str.slice(start, m.index), after: m.index + m[0].length };
      }
    }
  }
  return { body: str.slice(start), after: str.length };
}

export function render(template, context, partials = {}) {
  let out = "";
  let i = 0;
  const len = template.length;
  while (i < len) {
    const open = template.indexOf("{{", i);
    if (open === -1) {
      out += template.slice(i);
      break;
    }
    out += template.slice(i, open);
    const close = template.indexOf("}}", open);
    if (close === -1) {
      out += template.slice(open);
      break;
    }
    const tag = template.slice(open + 2, close).trim();
    const afterTag = close + 2;
    if (tag.startsWith("#")) {
      const name = tag.slice(1).trim();
      const { body, after } = findSection(template, afterTag);
      const value = lookup(context, name);
      if (Array.isArray(value)) {
        for (const item of value) {
          out += render(body, item, partials);
        }
      } else if (value && typeof value === "object") {
        out += render(body, Object.assign({}, context, value), partials);
      } else if (value) {
        out += render(body, context, partials);
      }
      i = after;
    } else if (tag.startsWith("^")) {
      const name = tag.slice(1).trim();
      const { body, after } = findSection(template, afterTag);
      const value = lookup(context, name);
      const truthy = Array.isArray(value) ? value.length > 0 : !!value;
      if (!truthy) {
        out += render(body, context, partials);
      }
      i = after;
    } else if (tag.startsWith("/")) {
      // stray closing
      i = afterTag;
    } else if (tag.startsWith(">")) {
      const pname = tag.slice(1).trim();
      const partial = partials[pname];
      if (partial != null) {
        out += render(String(partial), context, partials);
      }
      i = afterTag;
    } else if (tag.startsWith("!")) {
      i = afterTag;
    } else {
      const value = tag === "." ? context : lookup(context, tag);
      out += value == null ? "" : escapeHtml(value);
      i = afterTag;
    }
  }
  return out;
}
