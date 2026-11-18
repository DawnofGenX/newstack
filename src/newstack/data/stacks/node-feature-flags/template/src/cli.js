import { start } from './server.js';
import { bucket, resolveFlags, FLAGS } from './flags.js';

const args = process.argv.slice(2);
if (args[0] === 'serve') {
  start(Number(process.env.PORT) || 3000);
} else if (args[0] === 'eval') {
  const flag = args[1];
  const user = args[2];
  console.log(JSON.stringify({ flag, user, bucket: bucket(flag, user), enabled: resolveFlags(FLAGS, user)[flag] }));
} else if (args.includes('--help') || args.includes('-h')) {
  console.log('Usage: feature-flags serve | eval <flag> <user>');
  process.exit(0);
} else {
  // default serve
  start(Number(process.env.PORT) || 3000);
}
