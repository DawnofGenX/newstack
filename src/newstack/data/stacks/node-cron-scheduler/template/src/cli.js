import { parseArgs } from 'node:util';
import { createScheduler } from './scheduler.js';

const { values } = parseArgs({
  options: {
    store: { type: 'string', default: 'jobs.json' },
    name: { type: 'string', default: 'heartbeat' },
    schedule: { type: 'string', default: '* * * * * *' },
    duration: { type: 'string', default: '3000' },
  },
});

const scheduler = createScheduler(values.store);
let ticks = 0;
scheduler.register(values.name, values.schedule, () => {
  ticks += 1;
});
scheduler.start(values.name);
await new Promise((resolve) => setTimeout(resolve, Number(values.duration)));
scheduler.stop(values.name);
console.log(JSON.stringify(scheduler.snapshot(), null, 2));
console.log(`ticks=${ticks}`);