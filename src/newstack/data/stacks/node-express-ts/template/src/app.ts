import express, { type Request, type Response } from "express";

export interface Item {
  id: number;
  name: string;
}

export function createApp() {
  const app = express();
  app.use(express.json());

  const items: Item[] = [];
  let nextId = 1;

  app.get("/health", (_req: Request, res: Response) => {
    res.json({ status: "ok" });
  });

  app.get("/items", (_req: Request, res: Response) => {
    res.json(items);
  });

  app.post("/items", (req: Request, res: Response) => {
    const name = typeof req.body?.name === "string" ? req.body.name.trim() : "";
    if (!name) {
      res.status(400).json({ error: "name is required" });
      return;
    }
    const item: Item = { id: nextId++, name };
    items.push(item);
    res.status(201).json(item);
  });

  return app;
}
