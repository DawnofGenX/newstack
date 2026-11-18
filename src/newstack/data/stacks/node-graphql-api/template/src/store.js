let nextId = 1;
export const notes = [];

export function resetNotes() {
  notes.length = 0;
  nextId = 1;
}

export function allNotes() {
  return notes.map((note) => ({ ...note }));
}

export function addNote(title, body = '') {
  const note = { id: nextId++, title, body };
  notes.push(note);
  return { ...note };
}