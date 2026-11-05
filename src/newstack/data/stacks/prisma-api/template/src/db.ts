import path from 'node:path';
import { PrismaClient } from '@prisma/client';

export type NoteRow = { id: number; title: string; body: string };
const NOTE_SELECT = { id: true, title: true, body: true } as const;

export interface NoteStore {
  count(): Promise<number>;
  list(): Promise<NoteRow[]>;
  create(title: string, body: string): Promise<NoteRow>;
  get(id: number): Promise<NoteRow | null>;
  update(id: number, data: { title?: string; body?: string }): Promise<NoteRow | null>;
  remove(id: number): Promise<boolean>;
  disconnect(): Promise<void>;
}

// Prisma CLI resolves `file:./dev.db` in .env relative to prisma/schema.prisma,
// so the runtime default must resolve to the SAME absolute path (prisma/dev.db),
// not to cwd-relative ./dev.db. Divergence here is the classic SQLite trap.
export function dbUrl(): string {
  if (process.env.DATABASE_URL) return process.env.DATABASE_URL;
  const root = path.resolve(__dirname, '..', '..'); // dist/src -> svc root
  return 'file:' + path.join(root, 'prisma', 'dev.db');
}

export function createDb(url?: string): NoteStore {
  const prisma = new PrismaClient({ datasources: { db: { url: url ?? dbUrl() } } });
  return {
    count: () => prisma.note.count(),
    list: () => prisma.note.findMany({ orderBy: { id: 'asc' }, select: NOTE_SELECT }),
    create: (title, body) => prisma.note.create({ data: { title, body }, select: NOTE_SELECT }),
    get: (id) => prisma.note.findUnique({ where: { id }, select: NOTE_SELECT }),
    async update(id, data) {
      try {
        return await prisma.note.update({ where: { id }, data, select: NOTE_SELECT });
      } catch {
        return null; // P2025 (row not found) -> caller answers 404
      }
    },
    async remove(id) {
      try {
        await prisma.note.delete({ where: { id } });
        return true;
      } catch {
        return false;
      }
    },
    disconnect: () => prisma.$disconnect(),
  };
}
