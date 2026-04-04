-- Add source column to track which platform a job came from
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'pro360';
CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);

-- Rename pro360_url to job_url for multi-platform support
ALTER TABLE jobs RENAME COLUMN pro360_url TO job_url;

-- Rename pro360_path to path on categories (used for any platform)
ALTER TABLE categories RENAME COLUMN pro360_path TO path;

-- Add source column to categories
ALTER TABLE categories ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'pro360';

-- Tasker categories
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
