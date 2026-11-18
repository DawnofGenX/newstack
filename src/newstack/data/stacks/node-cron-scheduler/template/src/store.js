import fs from 'node:fs';

export function loadStore(path) {
  try {
    return JSON.parse(fs.readFileSync(path, 'utf8'));
  } catch {
    return { jobs: {} };
  }
}

export function saveStore(path, store) {
  fs.writeFileSync(path, JSON.stringify(store, null, 2) + '\n');
}