import { initTRPC } from "@trpc/server";
import { z } from "zod";

const t = initTRPC.create();

export const appRouter = t.router({
  health: t.procedure.query(() => ({ status: "ok" })),
  hello: t.procedure
    .input(z.object({ name: z.string().min(1) }))
    .query(({ input }) => `Hello ${input.name}`),
  add: t.procedure
    .input(z.object({ a: z.number(), b: z.number() }))
    .mutation(({ input }) => input.a + input.b),
});

export type AppRouter = typeof appRouter;