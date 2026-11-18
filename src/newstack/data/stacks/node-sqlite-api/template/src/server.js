import { createServer } from 'node:http';
import { openDatabase, listNotes, createNote, deleteNote, countNotes } from './notes.js';

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => { data += chunk; });
    req.on('end', () => resolve(data));
    req.on('error', reject);
  });
}

function send(res, status, body) {
  const payload = body === undefined ? '' : JSON.stringify(body);
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8' });
  res.end(payload);
}

export function buildServer(db = openDatabase()) {
  return createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
    const path = url.pathname;

    if (req.method === 'GET' && path === '/health') {
      return send(res, 200, { status: 'ok', notes: countNotes(db) });
    }

    if (req.method === 'GET' && path === '/notes') {
      return send(res, 200, { notes: listNotes(db) });
    }

    if (req.method === 'POST' && path === '/notes') {
      let parsed;
      try {
        parsed = JSON.parse(await readBody(req) || '{}');
      } catch {
        return send(res, 400, { error: 'invalid_json' });
      }
      const title = typeof parsed.title === 'string' ? parsed.title.trim() : '';
      const body = typeof parsed.body === 'string' ? parsed.body : '';
      if (!title) {
        return send(res, 400, { error: 'title_required' });
      }
      const note = createNote(db, title, body);
      return send(res, 201, note);
    }

    const match = path.match(/^\/notes\/(\d+)$/);
    if (match && req.method === 'DELETE') {
      const ok = deleteNote(db, Number(match[1]));
      if (!ok) return send(res, 404, { error: 'not_found' });
      res.writeHead(204);
      return res.end();
    }

    return send(res, 404, { error: 'not_found', detail: `no route for ${req.method} ${path}` });
  });
}

export function startServer(port = Number(process.env.PORT || 5550)) {
  const server = buildServer();
  server.listen(port, '127.0.0.1', () => {
    console.log(`node-sqlite-api listening on http://127.0.0.1:${port}`);
  });
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  startServer();
}