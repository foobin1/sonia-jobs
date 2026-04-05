import { FastifyInstance } from 'fastify';
import { z } from 'zod';
import { db } from '../db/client.js';
import { jobs } from '../db/schema.js';
import { env } from '../config.js';
import { translateText } from './translate.js';

const jobSchema = z.object({
  job_url: z.string().min(1),
  title: z.string().min(1),
  category: z.string().min(1),
  source: z.enum(['pro360', 'tasker']).default('pro360'),
  city: z.string().nullable().optional(),
  district: z.string().nullable().optional(),
  posted_at: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  budget: z.string().nullable().optional(),
  client_name: z.string().nullable().optional(),
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

    let body;
    try {
      body = ingestSchema.parse(request.body);
    } catch (err: any) {
      app.log.error({ err: err.message }, '[ingest] Validation error');
      return reply.status(400).send({ error: 'Validation failed', details: err.errors ?? err.message });
    }
    let inserted = 0;

    for (const job of body.jobs) {
      try {
        // Translate in background (fire-and-forget for speed)
        const titleEn = await translateText(job.title).catch(() => null);
        const descriptionEn = job.description
          ? await translateText(job.description.slice(0, 500)).catch(() => null)
          : null;
        const cityEn = job.city
          ? await translateText(job.city).catch(() => null)
          : null;

        await db.insert(jobs).values({
          jobUrl: job.job_url,
          title: job.title,
          category: job.category,
          source: job.source,
          city: job.city ?? null,
          district: job.district ?? null,
          postedAt: job.posted_at ? new Date(job.posted_at) : null,
          description: job.description ?? null,
          budget: job.budget ?? null,
          clientName: job.client_name ?? null,
          titleEn,
          descriptionEn,
          cityEn,
        }).onConflictDoUpdate({
          target: jobs.jobUrl,
          set: {
            title: job.title,
            category: job.category,
            description: job.description ?? null,
            budget: job.budget ?? null,
            city: job.city ?? null,
            district: job.district ?? null,
            postedAt: job.posted_at ? new Date(job.posted_at) : null,
            titleEn,
            descriptionEn,
            cityEn,
          },
        });
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
