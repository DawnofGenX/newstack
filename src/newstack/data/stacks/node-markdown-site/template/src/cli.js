import { parseArgs } from 'node:util';
import { buildSite } from './site.js';

const { values } = parseArgs({
  options: {
    input: { type: 'string', default: 'content' },
    output: { type: 'string', default: 'dist' },
  },
});

const count = buildSite(values.input, values.output);
console.log(`rendered ${count} page(s) to ${values.output}`);