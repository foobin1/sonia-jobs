import { Redis } from 'ioredis';
import { env } from '../config.js';

let redis: Redis | null = null;

function getRedis(): Redis | null {
  if (!env.REDIS_URL) return null;
  if (!redis) {
    redis = new Redis(env.REDIS_URL, { maxRetriesPerRequest: 1, lazyConnect: true });
    redis.on('error', (err: Error) => console.warn('[redis] Error:', err.message));
    redis.connect().catch(() => {});
  }
  return redis;
}

export async function cacheGet(key: string): Promise<string | null> {
  try {
    return await getRedis()?.get(key) ?? null;
  } catch { return null; }
}

export async function cacheSet(key: string, value: string, ttlSeconds: number): Promise<void> {
  try {
    await getRedis()?.setex(key, ttlSeconds, value);
  } catch { /* ignore */ }
}

export async function cacheDelete(pattern: string): Promise<void> {
  try {
    const r = getRedis();
    if (!r) return;
    const keys = await r.keys(pattern);
    if (keys.length) await r.del(...keys);
  } catch { /* ignore */ }
}
