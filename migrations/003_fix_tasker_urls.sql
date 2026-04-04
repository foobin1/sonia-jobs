-- Fix Tasker job URLs: /task/ → /cases/
UPDATE jobs
SET job_url = REPLACE(job_url, 'tasker.com.tw/task/', 'tasker.com.tw/cases/')
WHERE source = 'tasker' AND job_url LIKE '%tasker.com.tw/task/%';
