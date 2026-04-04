import { FastifyInstance } from 'fastify';
import { db } from '../db/client.js';
import { jobs, categories } from '../db/schema.js';
import { eq, desc, and, gte, ilike, or, sql, count } from 'drizzle-orm';

export function registerJobRoutes(app: FastifyInstance) {
  app.get('/api/jobs', async (request) => {
    const q = request.query as Record<string, string>;
    const page = Math.max(1, parseInt(q.page || '1'));
    const limit = Math.min(100, Math.max(1, parseInt(q.limit || '20')));
    const offset = (page - 1) * limit;

    const conditions: any[] = [];

    if (q.category) {
      conditions.push(eq(jobs.category, q.category));
    }
    if (q.city) {
      conditions.push(eq(jobs.city, q.city));
    }
    if (q.keyword) {
      const kw = `%${q.keyword}%`;
      conditions.push(or(ilike(jobs.title, kw), ilike(jobs.description, kw)));
    }
    if (q.hours) {
      const hours = parseInt(q.hours);
      if (hours > 0) {
        conditions.push(gte(jobs.scrapedAt, new Date(Date.now() - hours * 3600 * 1000)));
      }
    }

    const where = conditions.length ? and(...conditions) : undefined;

    const [data, [{ total }]] = await Promise.all([
      db.select().from(jobs).where(where).orderBy(desc(jobs.scrapedAt)).limit(limit).offset(offset),
      db.select({ total: count() }).from(jobs).where(where),
    ]);

    return {
      jobs: data,
      pagination: {
        page,
        limit,
        total: Number(total),
        pages: Math.ceil(Number(total) / limit),
      },
    };
  });
}
