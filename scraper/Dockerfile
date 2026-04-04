FROM python:3.12-slim
WORKDIR /app
COPY scraper/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY scraper/ .
CMD ["python", "-u", "scraper.py", "--backfill"]
