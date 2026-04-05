-- Ensure 'other' category exists for PRO360 classifier
INSERT INTO categories (slug, name_en, name_zh, path, source)
VALUES ('other', 'Other', '其他', '/case', 'pro360')
ON CONFLICT (slug) DO NOTHING;
