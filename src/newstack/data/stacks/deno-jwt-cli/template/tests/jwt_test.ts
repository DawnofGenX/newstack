import { sign, verify } from "../src/jwt.ts";

Deno.test("sign/verify roundtrip", async () => {
  const token = await sign({ sub: "user", foo: 42 }, "secret");
  const payload = await verify(token, "secret");
  if (!payload || payload.sub !== "user" || payload.foo !== 42) throw new Error("payload mismatch");
});

Deno.test("verify wrong secret fails", async () => {
  const token = await sign({ a: 1 }, "secret");
  const payload = await verify(token, "wrong");
  if (payload !== null) throw new Error("expected null");
});

Deno.test("verify tampered token fails", async () => {
  const token = await sign({ a: 1 }, "secret");
  const parts = token.split(".");
  parts[1] = parts[1] + "x";
  const tampered = parts.join(".");
  const payload = await verify(tampered, "secret");
  if (payload !== null) throw new Error("expected null");
});

Deno.test("verify expired token fails", async () => {
  const token = await sign({ exp: Math.floor(Date.now() / 1000) - 10 }, "secret");
  const payload = await verify(token, "secret");
  if (payload !== null) throw new Error("expected null");
});