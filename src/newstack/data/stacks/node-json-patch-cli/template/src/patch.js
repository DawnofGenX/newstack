function clone(v) {
  if (v === null || typeof v !== "object") return v;
  if (Array.isArray(v)) return v.map(clone);
  const out = {};
  for (const k of Object.keys(v)) out[k] = clone(v[k]);
  return out;
}

function parsePointer(pointer) {
  if (pointer === "") return [];
  if (!pointer.startsWith("/")) throw new Error("invalid pointer: " + pointer);
  return pointer
    .slice(1)
    .split("/")
    .map((seg) => seg.replace(/~1/g, "/").replace(/~0/g, "~"));
}

function get(doc, pointer) {
  const segs = parsePointer(pointer);
  let cur = doc;
  for (const seg of segs) {
    if (cur === null || typeof cur !== "object") throw new Error("path not found: " + pointer);
    if (Array.isArray(cur)) {
      if (seg === "-") throw new Error("invalid index '-' in get");
      const i = Number(seg);
      if (!Number.isInteger(i) || i < 0 || i >= cur.length) throw new Error("index out of range: " + pointer);
      cur = cur[i];
    } else {
      if (!(seg in cur)) throw new Error("path not found: " + pointer);
      cur = cur[seg];
    }
  }
  return cur;
}

function parentAndKey(doc, pointer) {
  const segs = parsePointer(pointer);
  if (segs.length === 0) return { parent: null, key: null, root: true };
  const last = segs[segs.length - 1];
  const parentPointer = "/" + segs.slice(0, -1).join("/");
  const parent = segs.length === 1 ? doc : get(doc, parentPointer === "/" ? "/" + segs.slice(0, -1).join("/") : parentPointer);
  // simpler:
  let cur = doc;
  for (let i = 0; i < segs.length - 1; i++) {
    const seg = segs[i];
    if (Array.isArray(cur)) {
      const idx = Number(seg);
      cur = cur[idx];
    } else {
      cur = cur[seg];
    }
  }
  return { parent: cur, key: last, root: false };
}

function setAtPath(doc, pointer, value) {
  if (pointer === "") return value;
  const { parent, key } = parentAndKey(doc, pointer);
  if (Array.isArray(parent)) {
    if (key === "-") {
      parent.push(value);
    } else {
      const idx = Number(key);
      if (!Number.isInteger(idx) || idx < 0 || idx > parent.length) throw new Error("invalid index");
      parent.splice(idx, 0, value);
    }
  } else {
    parent[key] = value;
  }
  return doc;
}

function removeAtPath(doc, pointer) {
  const { parent, key } = parentAndKey(doc, pointer);
  if (Array.isArray(parent)) {
    const idx = Number(key);
    if (!Number.isInteger(idx) || idx < 0 || idx >= parent.length) throw new Error("invalid index");
    parent.splice(idx, 1);
  } else {
    if (!(key in parent)) throw new Error("path not found");
    delete parent[key];
  }
}

export function applyPatch(doc, patch) {
  const out = clone(doc);
  if (!Array.isArray(patch)) throw new Error("patch must be an array");
  for (const op of patch) {
    const { op: operation } = op;
    switch (operation) {
      case "add": {
        setAtPath(out, op.path, clone(op.value));
        break;
      }
      case "remove": {
        // ensure exists
        get(out, op.path);
        removeAtPath(out, op.path);
        break;
      }
      case "replace": {
        get(out, op.path);
        // remove then add at same location (for arrays need index)
        const { parent, key } = parentAndKey(out, op.path);
        if (Array.isArray(parent)) {
          const idx = Number(key);
          parent[idx] = clone(op.value);
        } else {
          parent[key] = clone(op.value);
        }
        break;
      }
      case "move": {
        const val = clone(get(out, op.from));
        // remove from
        removeAtPath(out, op.from);
        setAtPath(out, op.path, val);
        break;
      }
      case "copy": {
        const val = clone(get(out, op.from));
        setAtPath(out, op.path, val);
        break;
      }
      case "test": {
        const actual = get(out, op.path);
        if (JSON.stringify(actual) !== JSON.stringify(op.value)) {
          throw new Error("test failed at " + op.path);
        }
        break;
      }
      default:
        throw new Error("unknown op: " + operation);
    }
  }
  return out;
}

// diff
function isObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

export function diff(a, b, basePath = "") {
  const ops = [];
  if (a === b) return ops;
  if (typeof a !== typeof b || Array.isArray(a) !== Array.isArray(b)) {
    ops.push({ op: "replace", path: basePath || "", value: clone(b) });
    return ops;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    // naive: if lengths differ or elements differ, replace whole array
    if (a.length !== b.length || a.some((v, i) => JSON.stringify(v) !== JSON.stringify(b[i]))) {
      // try element-wise add/remove? Simpler replace
      ops.push({ op: "replace", path: basePath || "", value: clone(b) });
    }
    return ops;
  }
  if (isObject(a) && isObject(b)) {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    for (const k of keys) {
      const p = basePath + "/" + escapePointer(k);
      if (!(k in a)) {
        ops.push({ op: "add", path: p, value: clone(b[k]) });
      } else if (!(k in b)) {
        ops.push({ op: "remove", path: p });
      } else {
        ops.push(...diff(a[k], b[k], p));
      }
    }
    return ops;
  }
  // primitives differ
  if (a !== b) {
    ops.push({ op: "replace", path: basePath || "", value: clone(b) });
  }
  return ops;
}

function escapePointer(seg) {
  return String(seg).replace(/~/g, "~0").replace(/\//g, "~1");
}