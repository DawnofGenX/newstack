// in-memory store for node-hono-api
export const items = new Map();
let nextId = 1;

export function createItem({ name, price }) {
  const id = String(nextId++);
  const item = { id, name, price: Number(price) };
  items.set(id, item);
  return item;
}

export function getItem(id) {
  return items.get(id) ?? null;
}

export function listItems() {
  return [...items.values()];
}

export function updateItem(id, patch) {
  const cur = items.get(id);
  if (!cur) return null;
  const next = { ...cur };
  if (patch && typeof patch === "object") {
    if (patch.name !== undefined) next.name = patch.name;
    if (patch.price !== undefined) next.price = Number(patch.price);
  }
  items.set(id, next);
  return next;
}

export function deleteItem(id) {
  return items.delete(id);
}

export function reset() {
  items.clear();
  nextId = 1;
}