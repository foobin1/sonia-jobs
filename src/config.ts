import { z } from 'zod';
import 'dotenv/config';

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  INGEST_KEY: z.string().min(16),
  REDIS_URL: z.string().url().optional(),
  PORT: z.coerce.number().default(3000),
});

export const env = envSchema.parse(process.env);
