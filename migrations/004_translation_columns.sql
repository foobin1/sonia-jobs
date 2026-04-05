-- Add English translation columns for job content
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS title_en TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS description_en TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS city_en TEXT;
