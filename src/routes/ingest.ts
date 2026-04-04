import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { db } from '../db/client.js';
import { jobs } from '../db/schema.js';
import { env } from '../config.js';
import { sql } from 'drizzle-orm';

const jobSchema = z.object({
  pro360_url: z.string().url(),
  title: z.string().min(1),
  category: z.string().min(1),
  city: z.string().optional(),
  district: z.string().optional(),
  posted_at: z.string().optional(),
  description: z.string().optional(),
  budget: z.string().optional(),
  client_name: z.string().optional(),
});

const ingestSchema = z.object({
  jobs: z.array(jobSchema).min(1).max(200),
});

export function registerIngestRoutes(app: FastifyInstance) {
  app.post('/api/ingest', async (request, reply) => {
    const key = request.headers['x-ingest-key'];
    if (key !== env.INGEST_KEY) {
      return reply.status(401).send({ error: 'Invalid ingest key' });
    }

    const body = ingestSchema.parse(request.body);
    let inserted = 0;

    for (const job of body.jobs) {
      try {
        await db.insert(jobs).values({
          pro360Url: job.pro360_url,
          title: job.title,
          category: job.category,
          city: job.city ?? null,
          district: job.district ?? null,
          postedAt: job.posted_at ? new Date(job.posted_at) : null,
          description: job.description ?? null,
          budget: job.budget ?? null,
          clientName: job.client_name ?? null,
        }).onConflictDoNothing({ target: jobs.pro360Url });
        inserted++;
      } catch (err: any) {
        // FK violation (bad category) — skip
        if (err.code === '23503') continue;
        throw err;
      }
    }

    return { inserted, total: body.jobs.length };
  });
}
