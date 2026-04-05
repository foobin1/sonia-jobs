import Fastify from 'fastify';
import fastifyStatic from '@fastify/static';
import path from 'node:path';
import { env } from './config.js';
import { runMigrations } from './db/migrate.js';
import { db } from './db/client.js';
import { jobs } from './db/schema.js';
import { lt, sql } from 'drizzle-orm';
import { registerIngestRoutes } from './routes/ingest.js';
import { registerJobRoutes } from './routes/jobs.js';
import { registerStatsRoutes } from './routes/stats.js';
import { registerTranslateRoutes } from './routes/translate.js';

const CLEANUP_DAYS = 7;
const CLEANUP_INTERVAL_MS = 6 * 60 * 60 * 1000; // 6 hours

async function cleanupOldJobs() {
  try {
    const cutoff = new Date(Date.now() - CLEANUP_DAYS * 24 * 60 * 60 * 1000);
    const result = await db.delete(jobs).where(lt(jobs.scrapedAt, cutoff));
    const count = result.rowCount ?? 0;
    if (count > 0) {
      console.log(`[cleanup] Deleted ${count} jobs older than ${CLEANUP_DAYS} days`);
    }
  } catch (err) {
    console.error('[cleanup] Error:', err);
  }
}

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
registerTranslateRoutes(app);

async function start() {
  try {
    console.log('[boot] Running migrations...');
    await runMigrations();
    console.log('[boot] Migrations complete');

    await app.listen({ port: env.PORT, host: '0.0.0.0' });
    console.log(`[boot] Server listening on port ${env.PORT}`);

    // Cleanup old jobs on startup and every 6 hours
    await cleanupOldJobs();
    setInterval(cleanupOldJobs, CLEANUP_INTERVAL_MS);
  } catch (err) {
    app.log.error(err);
    process.exit(1);
  }
}

start();
