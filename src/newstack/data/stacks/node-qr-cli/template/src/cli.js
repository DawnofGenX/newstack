import { parseArgs } from 'node:util';
import { generatePng, renderTerminal } from './qr.js';

const { values } = parseArgs({
  options: {
    text: { type: 'string', short: 't', default: 'https://example.com' },
    output: { type: 'string', short: 'o' },
    size: { type: 'string', default: '256' },
  },
});

if (values.output) {
  const file = await generatePng(values.text, values.output, { width: Number(values.size) });
  console.log(`wrote ${file}`);
} else {
  console.log(await renderTerminal(values.text));
}