import { pgTable, text, boolean, timestamp, uuid, index } from 'drizzle-orm/pg-core';

export const categories = pgTable('categories', {
  slug: text('slug').primaryKey(),
  nameEn: text('name_en').notNull(),
  nameZh: text('name_zh').notNull(),
  path: text('path').notNull(),
  source: text('source').notNull().default('pro360'),
  enabled: boolean('enabled').notNull().default(true),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
});

export const jobs = pgTable('jobs', {
  id: uuid('id').primaryKey().defaultRandom(),
  jobUrl: text('job_url').unique().notNull(),
  title: text('title').notNull(),
  category: text('category').notNull().references(() => categories.slug),
  source: text('source').notNull().default('pro360'),
  city: text('city'),
  district: text('district'),
  postedAt: timestamp('posted_at', { withTimezone: true }),
  description: text('description'),
  budget: text('budget'),
  clientName: text('client_name'),
  titleEn: text('title_en'),
  descriptionEn: text('description_en'),
  cityEn: text('city_en'),
  scrapedAt: timestamp('scraped_at', { withTimezone: true }).notNull().defaultNow(),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
}, (table) => [
  index('idx_jobs_category').on(table.category),
  index('idx_jobs_city').on(table.city),
  index('idx_jobs_source').on(table.source),
  index('idx_jobs_posted_at').on(table.postedAt),
  index('idx_jobs_scraped_at').on(table.scrapedAt),
]);
