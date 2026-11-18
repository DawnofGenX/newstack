import { Hono } from "hono";
import * as store from "./store.js";

export const app = new Hono();

app.get("/health", (c) => c.json({ ok: true }));

app.get("/items", (c) => c.json(store.listItems()));

app.get("/items/:id", (c) => {
  const item = store.getItem(c.req.param("id"));
  if (!item) return c.json({ error: "not found" }, 404);
  return c.json(item);
});

app.post("/items", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  if (!body || typeof body.name !== "string" || body.name.trim() === "") {
    return c.json({ error: "name required" }, 400);
  }
  const item = store.createItem({ name: body.name, price: body.price ?? 0 });
  return c.json(item, 201);
});

app.put("/items/:id", async (c) => {
  const body = await c.req.json().catch(() => ({}));
  const updated = store.updateItem(c.req.param("id"), body);
  if (!updated) return c.json({ error: "not found" }, 404);
  return c.json(updated);
});

app.delete("/items/:id", (c) => {
  const ok = store.deleteItem(c.req.param("id"));
  if (!ok) return c.json({ error: "not found" }, 404);
  return c.body(null, 204);
});