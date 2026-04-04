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
    const source = q.source || null;

    const sourceFilter = source ? `AND j.source = '${source}'` : '';
    const sourceFilterShort = source ? `AND source = '${source}'` : '';

    const [byCategory, byCity, hourly, totals, bySource] = await Promise.all([
      pool.query(
        `SELECT j.category, c.name_en, c.name_zh, j.source, COUNT(*)::int as count
         FROM jobs j JOIN categories c ON j.category = c.slug
         WHERE j.scraped_at >= $1 ${sourceFilter}
         GROUP BY j.category, c.name_en, c.name_zh, j.source
         ORDER BY count DESC`, [since]
      ),
      pool.query(
        `SELECT city, COUNT(*)::int as count
         FROM jobs WHERE scraped_at >= $1 AND city IS NOT NULL ${sourceFilterShort}
         GROUP BY city ORDER BY count DESC LIMIT 15`, [since]
      ),
      pool.query(
        `SELECT date_trunc('hour', scraped_at) as hour, COUNT(*)::int as count
         FROM jobs WHERE scraped_at >= $1 ${sourceFilterShort}
         GROUP BY hour ORDER BY hour`, [since]
      ),
      pool.query(
        `SELECT COUNT(*)::int as total,
                COUNT(*) FILTER (WHERE scraped_at >= $1)::int as recent
         FROM jobs WHERE 1=1 ${sourceFilterShort}`, [since]
      ),
      pool.query(
        `SELECT source, COUNT(*)::int as count
         FROM jobs WHERE scraped_at >= $1
         GROUP BY source ORDER BY count DESC`, [since]
      ),
    ]);

    return {
      byCategory: byCategory.rows,
      byCity: byCity.rows,
      hourly: hourly.rows,
      bySource: bySource.rows,
      total: totals.rows[0]?.total ?? 0,
      recent: totals.rows[0]?.recent ?? 0,
    };
  });

  app.get('/api/categories', async (request) => {
    const q = request.query as Record<string, string>;
    if (q.source) {
      return db.select().from(categories).where(eq(categories.source, q.source));
    }
    return db.select().from(categories).where(eq(categories.enabled, true));
  });

  app.get('/health', async () => {
    return { status: 'ok', timestamp: new Date().toISOString() };
  });
}
