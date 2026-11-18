const base = process.env.BASE_URL || `http://127.0.0.1:${process.env.PORT || 5550}`;
let failures = 0;
function check(name, ok, detail = '') {
  if (ok) console.log(`ok ${name}`);
  else { failures++; console.log(`FAIL ${name}${detail ? ': ' + detail : ''}`); }
}

const health = await (await fetch(`${base}/health`)).json();
check('health status', health.status === 'ok');

const created = await (await fetch(`${base}/notes`, {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ title: 'contract', body: 'hello' }),
})).json();
check('create id', typeof created.id === 'number');

const list = await (await fetch(`${base}/notes`)).json();
check('list contains note', Array.isArray(list.notes) && list.notes.some((n) => n.id === created.id));

const del = await fetch(`${base}/notes/${created.id}`, { method: 'DELETE' });
check('delete status', del.status === 204);

const missing = await fetch(`${base}/notes/${created.id}`, { method: 'DELETE' });
check('delete missing 404', missing.status === 404);

console.log(failures === 0 ? 'all sqlite checks passed' : `${failures} sqlite check(s) failed`);
process.exit(failures === 0 ? 0 : 1);