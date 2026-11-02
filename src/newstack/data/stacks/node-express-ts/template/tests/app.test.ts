import request from "supertest";
import { describe, expect, it } from "vitest";

import { createApp } from "../src/app";

describe("api", () => {
  it("answers the health check", async () => {
    const response = await request(createApp()).get("/health");
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ status: "ok" });
  });

  it("starts with no items", async () => {
    const response = await request(createApp()).get("/items");
    expect(response.body).toEqual([]);
  });

  it("creates an item and lists it", async () => {
    const app = createApp();
    const created = await request(app).post("/items").send({ name: "pen" });
    expect(created.status).toBe(201);
    expect(created.body).toEqual({ id: 1, name: "pen" });

    const listed = await request(app).get("/items");
    expect(listed.body).toHaveLength(1);
  });

  it("rejects an item without a name", async () => {
    const response = await request(createApp()).post("/items").send({});
    expect(response.status).toBe(400);
  });
});
