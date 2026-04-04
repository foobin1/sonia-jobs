import fs from 'node:fs';
import path from 'node:path';
import { pool } from './client.js';

export async function runMigrations(): Promise<void> {
  const migrationsDir = path.resolve(process.cwd(), 'migrations');
  const files = fs.readdirSync(migrationsDir).filter(f => f.endsWith('.sql')).sort();

  for (const file of files) {
    const sql = fs.readFileSync(path.join(migrationsDir, file), 'utf-8');
    console.log(`[migrate] Running ${file}...`);
    await pool.query(sql);
    console.log(`[migrate] Done ${file}`);
  }
}
