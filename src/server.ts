import Fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import path from 'node:path';
import { env } from './config.js';
import { runMigrations } from './db/migrate.js';
import { registerIngestRoutes } from './routes/ingest.js';
import { registerJobRoutes } from './routes/jobs.js';
import { registerStatsRoutes } from './routes/stats.js';

const app = Fastify({ logger: true });

// Serve static dashboard
app.register(fastifyStatic, {
  root: path.resolve(process.cwd(), 'public'),
  prefix: '/',
});

// Routes
registerIngestRoutes(app);
registerJobRoutes(app);
registerStatsRoutes(app);

async function start() {
  try {
    console.log('[boot] Running migrations...');
    await runMigrations();
    console.log('[boot] Migrations complete');

    await app.listen({ port: env.PORT, host: '0.0.0.0' });
    console.log(`[boot] Server listening on port ${env.PORT}`);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

start();
