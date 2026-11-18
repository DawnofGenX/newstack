import cron from 'node-cron';
import { loadStore, saveStore } from './store.js';

export function createScheduler(storePath) {
  const store = loadStore(storePath);
  const entries = new Map();

  function stateFor(name, schedule) {
    if (!store.jobs[name]) {
      store.jobs[name] = { schedule, runs: 0, lastRun: null, lastError: null };
    }
    store.jobs[name].schedule = schedule;
    return store.jobs[name];
  }

  return {
    register(name, schedule, task) {
      const state = stateFor(name, schedule);
      const cronTask = cron.schedule(schedule, async () => {
        state.lastRun = new Date().toISOString();
        try {
          await task();
          state.runs += 1;
          state.lastError = null;
        } catch (error) {
          state.lastError = String(error?.message ?? error);
        }
        saveStore(storePath, store);
      }, { scheduled: false });
      entries.set(name, { schedule, cronTask, state });
      saveStore(storePath, store);
      return entries.get(name);
    },
    start(name) {
      if (name) entries.get(name)?.cronTask.start();
      else for (const entry of entries.values()) entry.cronTask.start();
    },
    stop(name) {
      if (name) entries.get(name)?.cronTask.stop();
      else for (const entry of entries.values()) entry.cronTask.stop();
    },
    runNow(name) {
      const entry = entries.get(name);
      if (!entry) throw new Error(`unknown job: ${name}`);
      return entry.cronTask.now ? entry.cronTask.now() : undefined;
    },
    snapshot() {
      return store;
    },
  };
}