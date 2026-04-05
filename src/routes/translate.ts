import { FastifyInstance } from 'fastify';

// In-memory translation cache (persists until restart)
const cache = new Map<string, string>();

async function translateText(text: string): Promise<string> {
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
    // Response format: [[["translated","original",null,null,10],...],null,"zh-TW"]
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
  // Batch translate texts
  app.post('/api/translate', async (request, reply) => {
    const body = request.body as { texts?: string[] };
    if (!body.texts || !Array.isArray(body.texts)) {
      return reply.status(400).send({ error: 'texts array required' });
    }

    // Limit batch size
    const texts = body.texts.slice(0, 50);

    // Translate in parallel (max 5 concurrent)
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
}
