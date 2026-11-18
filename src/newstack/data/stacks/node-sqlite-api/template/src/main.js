import { startServer } from './server.js';

const port = Number(process.env.PORT || 5550);
startServer(port);