import express, { type Express, type Request, type Response, type NextFunction } from 'express';
import type { NoteStore } from './db';

function parseId(raw: string | string[] | undefined): number | null {
  const s = Array.isArray(raw) ? raw[0] : raw ?? '';
  if (!/^\d+$/.test(s)) return null;
  const n = Number(s);
  return Number.isSafeInteger(n) ? n : null;
}

// title must be a non-blank string; body defaults to "" when absent,
// and any non-string body is coerced to "" (contract is silent on those).
function validateTitle(v: unknown): string | null {
  if (typeof v !== 'string') return null;
  const t = v.trim();
  return t.length > 0 ? v : null;
}

export function buildApp(db: NoteStore): Express {
  const app = express();
  app.use(express.json());

  // Explicit method dispatch per route => unknown methods get 405, not fall-through 404.
  app.all('/health', async (req: Request, res: Response, next: NextFunction) => {
    if (req.method !== 'GET') {
      res.status(405).json({ error: 'method_not_allowed' });
      return;
    }
    try {
      const notes = await db.count();
      res.status(200).json({ status: 'ok', notes });
    } catch (err) {
      next(err);
    }
  });

  app.all('/notes', async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (req.method === 'GET') {
        res.status(200).json(await db.list());
        return;
      }
      if (req.method === 'POST') {
        const body = (req.body ?? {}) as Record<string, unknown>;
        const title = validateTitle(body.title);
        if (title === null) {
          res.status(422).json({ error: 'invalid_title' });
          return;
        }
        const note = await db.create(title, typeof body.body === 'string' ? body.body : '');
        res.status(201).json(note);
        return;
      }
      res.status(405).json({ error: 'method_not_allowed' });
    } catch (err) {
      next(err);
    }
  });

  app.all('/notes/:id', async (req: Request, res: Response, next: NextFunction) => {
    const rawId = Array.isArray(req.params.id) ? req.params.id[0] : req.params.id;
    const id = parseId(rawId);
    const notFound = () => res.status(404).json({ error: 'not_found', detail: `no note with id ${rawId}` });
    try {
      if (req.method === 'GET') {
        const note = id === null ? null : await db.get(id);
        if (!note) { notFound(); return; }
        res.status(200).json(note);
        return;
      }
      if (req.method === 'PATCH') {
        const body = (req.body ?? {}) as Record<string, unknown>;
        let title: string | undefined;
        if ('title' in body) {
          const t = validateTitle(body.title);
          if (t === null) {
            res.status(422).json({ error: 'invalid_title' });
            return;
          }
          title = t;
        }
        const data: { title?: string; body?: string } = {};
        if (title !== undefined) data.title = title;
        if (typeof body.body === 'string') data.body = body.body;
        if (Object.keys(data).length === 0) {
          const cur = id === null ? null : await db.get(id);
          if (!cur) { notFound(); return; }
          res.status(200).json(cur); // no-op patch: untouched
          return;
        }
        const note = id === null ? null : await db.update(id, data);
        if (!note) { notFound(); return; }
        res.status(200).json(note);
        return;
      }
      if (req.method === 'DELETE') {
        if (id === null || !(await db.remove(id))) { notFound(); return; }
        res.status(204).end();
        return;
      }
      res.status(405).json({ error: 'method_not_allowed' });
    } catch (err) {
      next(err);
    }
  });

  // unknown route -> 404 (path without query)
  app.use((req: Request, res: Response) => {
    res.status(404).json({ error: 'not_found', detail: `no route for ${req.method} ${req.path}` });
  });

  // express.json() throws SyntaxError on malformed bodies -> 422 invalid_json
  app.use((err: unknown, _req: Request, res: Response, _next: NextFunction) => {
    if (err instanceof SyntaxError && 'body' in (err as object)) {
      res.status(422).json({ error: 'invalid_json' });
      return;
    }
    console.error(err);
    res.status(500).json({ error: 'internal_error' });
  });

  return app;
}
