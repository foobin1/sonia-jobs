import { FastifyInstance } from 'fastify';
import { pool } from '../db/client.js';
import { db } from '../db/client.js';
import { categories } from '../db/schema.js';
import { eq } from 'drizzle-orm';

export function registerStatsRoutes(app: FastifyInstance) {
  app.get('/api/stats', async (request) => {
    const q = request.query as Record<string, string>;
    const hours = parseInt(q.hours || '24');
    const since = new Date(Date.now() - hours * 3600 * 1000).toISOString();

    const [byCategory, byCity, hourly, totals] = await Promise.all([
      pool.query(
        `SELECT j.category, c.name_en, c.name_zh, COUNT(*)::int as count
         FROM jobs j JOIN categories c ON j.category = c.slug
         WHERE j.scraped_at >= $1
         GROUP BY j.category, c.name_en, c.name_zh
         ORDER BY count DESC`, [since]
      ),
      pool.query(
        `SELECT city, COUNT(*)::int as count
         FROM jobs WHERE scraped_at >= $1 AND city IS NOT NULL
         GROUP BY city ORDER BY count DESC LIMIT 15`, [since]
      ),
      pool.query(
        `SELECT date_trunc('hour', scraped_at) as hour, COUNT(*)::int as count
         FROM jobs WHERE scraped_at >= $1
         GROUP BY hour ORDER BY hour`, [since]
      ),
      pool.query(
        `SELECT COUNT(*)::int as total,
                COUNT(*) FILTER (WHERE scraped_at >= $1)::int as recent
         FROM jobs`, [since]
      ),
    ]);

    return {
      byCategory: byCategory.rows,
      byCity: byCity.rows,
      hourly: hourly.rows,
      total: totals.rows[0]?.total ?? 0,
      recent: totals.rows[0]?.recent ?? 0,
    };
  });

  app.get('/api/categories', async () => {
    return db.select().from(categories).where(eq(categories.enabled, true));
  });

  app.get('/health', async () => {
    return { status: 'ok', timestamp: new Date().toISOString() };
  });
}
