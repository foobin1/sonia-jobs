import { FastifyInstance } from 'fastify';
import { db } from '../db/client.js';
import { jobs } from '../db/schema.js';
import { isNull, sql } from 'drizzle-orm';
import { env } from '../config.js';

// In-memory translation cache (persists until restart)
const cache = new Map<string, string>();

export async function translateText(text: string): Promise<string> {
  if (!text || text.length === 0) return text;
  const cached = cache.get(text);
  if (cached) return cached;

  try {
    const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=zh-TW&tl=en&dt=t&q=${encodeURIComponent(text)}`;
    const res = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
    });
    if (!res.ok) return text;
    const data = await res.json() as any;
    const translated = (data[0] as any[])
      .filter((seg: any) => seg && seg[0])
      .map((seg: any) => seg[0])
      .join('');
    if (translated) {
      cache.set(text, translated);
      return translated;
    }
    return text;
  } catch {
    return text;
  }
}

export function registerTranslateRoutes(app: FastifyInstance) {
  // Batch translate texts (used by frontend for ad-hoc translation)
  app.post('/api/translate', async (request, reply) => {
    const body = request.body as { texts?: string[] };
    if (!body.texts || !Array.isArray(body.texts)) {
      return reply.status(400).send({ error: 'texts array required' });
    }

    const texts = body.texts.slice(0, 50);
    const results: string[] = [];
    for (let i = 0; i < texts.length; i += 5) {
      const batch = texts.slice(i, i + 5);
      const translated = await Promise.all(
        batch.map(t => translateText((t || '').slice(0, 500)))
      );
      results.push(...translated);
    }

    return { translations: results };
  });

  // Backfill translations for all untranslated jobs
  app.post('/api/translate/backfill', async (request, reply) => {
    const key = request.headers['x-ingest-key'];
    if (key !== env.INGEST_KEY) {
      return reply.status(401).send({ error: 'Invalid ingest key' });
    }

    // Find jobs missing translations
    const untranslated = await db.select({
      id: jobs.id,
      title: jobs.title,
      description: jobs.description,
      city: jobs.city,
    }).from(jobs).where(isNull(jobs.titleEn)).limit(50);

    if (untranslated.length === 0) {
      return { message: 'All jobs translated', remaining: 0 };
    }

    let translated = 0;
    for (const job of untranslated) {
      try {
        const [titleEn, descriptionEn, cityEn] = await Promise.all([
          translateText(job.title),
          job.description ? translateText(job.description.slice(0, 500)) : Promise.resolve(null),
          job.city ? translateText(job.city) : Promise.resolve(null),
        ]);

        await db.update(jobs).set({
          titleEn,
          descriptionEn,
          cityEn,
        }).where(sql`${jobs.id} = ${job.id}`);

        translated++;
        // Small delay to avoid rate limiting
        await new Promise(r => setTimeout(r, 200));
      } catch (err) {
        console.error(`[translate] Failed for job ${job.id}:`, err);
      }
    }

    // Check remaining
    const [{ count }] = await db.select({
      count: sql<number>`count(*)`,
    }).from(jobs).where(isNull(jobs.titleEn));

    return { translated, remaining: Number(count) };
  });
}
