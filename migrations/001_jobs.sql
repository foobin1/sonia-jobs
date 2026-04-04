-- Categories for job platforms
CREATE TABLE IF NOT EXISTS categories (
  slug        TEXT PRIMARY KEY,
  name_en     TEXT NOT NULL,
  name_zh     TEXT NOT NULL,
  path        TEXT NOT NULL,
  source      TEXT NOT NULL DEFAULT 'pro360',
  enabled     BOOLEAN NOT NULL DEFAULT true,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Scraped job listings
CREATE TABLE IF NOT EXISTS jobs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_url      TEXT UNIQUE NOT NULL,
  title        TEXT NOT NULL,
  category     TEXT NOT NULL REFERENCES categories(slug),
  source       TEXT NOT NULL DEFAULT 'pro360',
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
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

-- Seed PRO360 categories
INSERT INTO categories (slug, name_en, name_zh, path, source) VALUES
  ('cleaning',     'Cleaning',              '清潔服務', '/case/subgenre/cleaning',     'pro360'),
  ('handyman',     'Plumbing & Electrical', '水電工程', '/case/subgenre/handyman',     'pro360'),
  ('moving',       'Moving',               '搬家回收', '/case/subgenre/moving',        'pro360'),
  ('tutoring',     'Tutoring',             '家教',     '/case/subgenre/tutoring',      'pro360'),
  ('design',       'Graphic Design',       '平面設計', '/case/subgenre/design',        'pro360'),
  ('photography',  'Photography',          '攝影服務', '/case/subgenre/photography',   'pro360'),
  ('renovation',   'Renovation',           '裝潢設計', '/case/subgenre/renovation',    'pro360'),
  ('pest_control', 'Pest Control',         '消毒除蟲', '/case/subgenre/pest_control',  'pro360'),
  ('ac_repair',    'AC Repair',            '冷氣維修', '/case/subgenre/ac_repair',     'pro360'),
  ('web_dev',      'Web Development',      '網頁程式', '/case/subgenre/web_dev',       'pro360')
ON CONFLICT (slug) DO NOTHING;

-- Seed Tasker categories
INSERT INTO categories (slug, name_en, name_zh, path, source, enabled) VALUES
  ('tasker_design',      'Design',            '商業設計',   '/cases/top',  'tasker', true),
  ('tasker_marketing',   'Marketing',         '行銷企劃',   '/cases/top',  'tasker', true),
  ('tasker_it',          'IT & Programming',  '資訊工程',   '/cases/top',  'tasker', true),
  ('tasker_writing',     'Writing',           '文字創作',   '/cases/top',  'tasker', true),
  ('tasker_video',       'Video & Audio',     '影音製作',   '/cases/top',  'tasker', true),
  ('tasker_translation', 'Translation',       '翻譯語言',   '/cases/top',  'tasker', true),
  ('tasker_accounting',  'Accounting',        '會計記帳',   '/cases/top',  'tasker', true),
  ('tasker_lifestyle',   'Lifestyle',         '生活服務',   '/cases/top',  'tasker', true),
  ('tasker_ai',          'AI',               'AI應用',     '/cases/top',  'tasker', true),
  ('tasker_other',       'Other',            '其他',       '/cases/top',  'tasker', true)
ON CONFLICT (slug) DO NOTHING;
