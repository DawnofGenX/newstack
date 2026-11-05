// Storage for resumable uploads: one file per upload, plus an index the process
// can reopen. The index is the authority on how many bytes are on disk, so it is
// written with a temp file and a rename — a truncated index would make the next
// boot trust a size the file does not have.
import { createHash, randomBytes } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, open, rename, rm, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

export const MAX_SIZE = 1024 * 1024;
const INDEX = "sessions.json";

export class UploadStore {
  constructor(root) {
    this.root = root;
    this.sessions = new Map();
    this.hashes = new Map();
  }

  static async open(root) {
    const store = new UploadStore(root);
    await mkdir(root, { recursive: true });
    let raw;
    try {
      raw = await readFile(path.join(root, INDEX), "utf8");
    } catch (error) {
      if (error.code === "ENOENT") return store;
      throw error;
    }
    // A corrupt index is a hard stop: starting empty would strand every file on
    // disk and then overwrite the record of them on the next upload.
    const loaded = JSON.parse(raw);
    for (const session of loaded) {
      store.sessions.set(session.id, { ...session });
    }
    return store;
  }

  get(id) {
    return this.sessions.get(id);
  }

  count() {
    return this.sessions.size;
  }

  create(name, size) {
    const id = randomBytes(8).toString("hex");
    const session = { id, name, size, received: 0, complete: false, digest: null };
    this.sessions.set(id, session);
    return session;
  }

  file(id) {
    return path.join(this.root, `${id}.bin`);
  }

  // hashFor returns the running SHA-256, rebuilding it from the file after a
  // restart. A hash object cannot be serialised, so the disk is the only record
  // of the bytes that arrived before the process died.
  async hashFor(session) {
    let hash = this.hashes.get(session.id);
    if (hash) return hash;
    hash = createHash("sha256");
    if (session.received > 0) {
      for await (const chunk of createReadStream(this.file(session.id))) {
        hash.update(chunk);
      }
    }
    this.hashes.set(session.id, hash);
    return hash;
  }

  // write appends at the recorded offset, not at the end of the file: if the two
  // ever disagree, writing at the end would silently glue a replayed chunk onto
  // the wrong place instead of failing the offset check.
  async write(session, chunk) {
    // The hash is rebuilt from the file *before* the new chunk lands: hashFor
    // reads everything on disk, so calling it afterwards would hash the fresh
    // bytes twice and report a digest no client can reproduce.
    const hash = await this.hashFor(session);
    const file = this.file(session.id);
    const handle = await open(file, session.received === 0 ? "w" : "r+");
    try {
      await handle.write(chunk, 0, chunk.length, session.received);
    } finally {
      await handle.close();
    }
    hash.update(chunk);
    session.received += chunk.length;
    if (session.received === session.size) {
      session.complete = true;
      session.digest = hash.digest("hex");
      this.hashes.delete(session.id);
    }
    await this.save();
    return session;
  }

  async read(id) {
    const session = this.sessions.get(id);
    if (!session) return null;
    return readFile(this.file(id));
  }

  async remove(id) {
    const session = this.sessions.get(id);
    if (!session) return false;
    this.sessions.delete(id);
    this.hashes.delete(id);
    await rm(this.file(id), { force: true });
    await this.save();
    return true;
  }

  async save() {
    const payload = JSON.stringify([...this.sessions.values()], null, 2);
    const temp = path.join(this.root, `.${INDEX}.${process.pid}.tmp`);
    await writeFile(temp, payload, "utf8");
    await rename(temp, path.join(this.root, INDEX));
  }
}
