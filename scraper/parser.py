"""Parse PRO360 job listing pages."""

import re
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from config import BASE_URL

TW_TZ = timezone(timedelta(hours=8))


def parse_relative_time(text: str) -> str | None:
    """Convert '5分鐘前', '2小時前', '1天前' to ISO timestamp."""
    now = datetime.now(TW_TZ)
    text = text.strip()

    m = re.search(r'(\d+)\s*分鐘前', text)
    if m:
        return (now - timedelta(minutes=int(m.group(1)))).isoformat()

    m = re.search(r'(\d+)\s*小時前', text)
    if m:
        return (now - timedelta(hours=int(m.group(1)))).isoformat()

    m = re.search(r'(\d+)\s*天前', text)
    if m:
        return (now - timedelta(days=int(m.group(1)))).isoformat()

    # Try "YYYY/MM/DD" format
    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
    if m:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TW_TZ)
        return dt.isoformat()

    return None


def parse_location(text: str) -> tuple[str | None, str | None]:
    """Split location string into (city, district)."""
    text = text.strip()
    if not text:
        return None, None

    # Common pattern: "台北市中山區" or "台北市 中山區"
    m = re.match(r'(.+?[市縣])(.+?[區鄉鎮市])?', text)
    if m:
        return m.group(1), m.group(2)

    return text, None


def parse_jobs_page(html: str, category: str) -> list[dict]:
    """Parse a PRO360 category page and return job dicts."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    cards = soup.select('.div_request_card')
    if not cards:
        # Try alternative selectors
        cards = soup.select('[class*="request_card"]')

    for card in cards:
        try:
            job = parse_single_card(card, category)
            if job:
                results.append(job)
        except Exception as e:
            print(f"  [parser] Error parsing card: {e}")
            continue

    return results


def parse_single_card(card, category: str) -> dict | None:
    """Parse a single job card element."""
    # Title
    title_el = card.select_one('.title_text') or card.select_one('h3') or card.select_one('[class*="title"]')
    if not title_el:
        return None
    title = title_el.get_text(strip=True)
    if not title:
        return None

    # URL
    link = card.select_one('a[href]')
    url = None
    if link:
        href = link.get('href', '')
        if href.startswith('/'):
            url = BASE_URL + href
        elif href.startswith('http'):
            url = href

    if not url:
        return None

    # Location (near location icon)
    city, district = None, None
    loc_icon = card.select_one('.icon_location_circle')
    if loc_icon:
        loc_text = loc_icon.find_next(string=True)
        if loc_text:
            city, district = parse_location(loc_text.strip())
    if not city:
        # Fallback: look for any element with location-like text
        for el in card.select('span, div, p'):
            text = el.get_text(strip=True)
            if re.match(r'.+[市縣]', text) and len(text) < 20:
                city, district = parse_location(text)
                break

    # Time
    posted_at = None
    time_icon = card.select_one('.icon_time_circle')
    if time_icon:
        time_text = time_icon.find_next(string=True)
        if time_text:
            posted_at = parse_relative_time(time_text.strip())
    if not posted_at:
        for el in card.select('span, div'):
            text = el.get_text(strip=True)
            if re.search(r'(分鐘前|小時前|天前|\d{4}/\d)', text):
                posted_at = parse_relative_time(text)
                break

    # Budget
    budget = None
    budget_icon = card.select_one('.icon_dollar_circle')
    if budget_icon:
        budget_text = budget_icon.find_next(string=True)
        if budget_text:
            budget = budget_text.strip()
    if not budget:
        for el in card.select('span, div'):
            text = el.get_text(strip=True)
            if re.search(r'(\$|元|NT|面議|\d+,\d+)', text) and len(text) < 30:
                budget = text
                break

    # Description
    description = None
    desc_el = card.select_one('.div_request_card_second') or card.select_one('[class*="desc"]')
    if desc_el:
        description = desc_el.get_text(strip=True)[:500]

    # Client name
    client_name = None
    name_el = card.select_one('[class*="name"]') or card.select_one('[class*="client"]')
    if name_el:
        client_name = name_el.get_text(strip=True)

    return {
        "pro360_url": url,
        "title": title,
        "category": category,
        "city": city,
        "district": district,
        "posted_at": posted_at,
        "description": description,
        "budget": budget,
        "client_name": client_name,
    }
