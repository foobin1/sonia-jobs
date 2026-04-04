-- Categories for PRO360 subgenres
CREATE TABLE IF NOT EXISTS categories (
  slug        TEXT PRIMARY KEY,
  name_en     TEXT NOT NULL,
  name_zh     TEXT NOT NULL,
  pro360_path TEXT NOT NULL,
  enabled     BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Scraped job listings
CREATE TABLE IF NOT EXISTS jobs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pro360_url   TEXT UNIQUE NOT NULL,
  title        TEXT NOT NULL,
  category     TEXT NOT NULL REFERENCES categories(slug),
  city         TEXT,
  district     TEXT,
  posted_at    TIMESTAMPTZ,
  description  TEXT,
  budget       TEXT,
  client_name  TEXT,
  scraped_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at DESC);

-- Seed initial categories
INSERT INTO categories (slug, name_en, name_zh, pro360_path) VALUES
  ('cleaning',     'Cleaning',        '清潔服務', '/case/subgenre/cleaning'),
  ('handyman',     'Plumbing & Electrical', '水電工程', '/case/subgenre/handyman'),
  ('moving',       'Moving',          '搬家回收', '/case/subgenre/moving'),
  ('tutoring',     'Tutoring',        '家教',     '/case/subgenre/tutoring'),
  ('design',       'Graphic Design',  '平面設計', '/case/subgenre/design'),
  ('photography',  'Photography',     '攝影服務', '/case/subgenre/photography'),
  ('renovation',   'Renovation',      '裝潢設計', '/case/subgenre/renovation'),
  ('pest_control', 'Pest Control',    '消毒除蟲', '/case/subgenre/pest_control'),
  ('ac_repair',    'AC Repair',       '冷氣維修', '/case/subgenre/ac_repair'),
  ('web_dev',      'Web Development', '網頁程式', '/case/subgenre/web_dev')
ON CONFLICT (slug) DO NOTHING;
