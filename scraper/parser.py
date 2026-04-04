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

    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
    if m:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TW_TZ)
        return dt.isoformat()

    return None


def parse_location(text: str) -> tuple[str | None, str | None]:
    """Split '新北市 三重區' into (city, district)."""
    text = text.strip()
    if not text:
        return None, None

    # PRO360 uses space-separated: "新北市 三重區"
    parts = text.split()
    if len(parts) >= 2:
        return parts[0], parts[1]

    # Fallback: "台北市中山區"
    m = re.match(r'(.+?[市縣])(.+?[區鄉鎮市])?', text)
    if m:
        return m.group(1), m.group(2)

    return text, None


def parse_jobs_page(html: str, category: str) -> list[dict]:
    """Parse a PRO360 category page and return job dicts."""
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    # Cards are <section class="div_request_card">
    cards = soup.select('section.div_request_card')
    if not cards:
        cards = soup.select('.div_request_card')

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
    """Parse a single PRO360 job card.

    Structure:
    - section.div_request_card
      - div.div_request_card_first
        - h2: title (e.g. "窗簾清潔")
        - span: client name (e.g. "莊〇生")
        - img[alt="地區"] + text: location
        - img[alt="金額"] + text: budget info
        - div with "XX分鐘前": time
      - div.div_request_card_second
        - spans: description fragments
      - div.request_card_footer
        - a[href*="/case/request/"]: unique job URL
    """

    # === URL (from footer — this is the unique job identifier) ===
    url = None
    footer_link = card.select_one('.request_card_footer a[href*="/case/request/"]')
    if footer_link:
        href = footer_link.get('href', '')
        if href.startswith('http'):
            url = href
        elif href.startswith('/'):
            url = BASE_URL + href
    if not url:
        # Try any link with /case/request/
        for a in card.select('a[href]'):
            href = a.get('href', '')
            if '/case/request/' in href:
                url = href if href.startswith('http') else BASE_URL + href
                break
    if not url:
        return None

    # === Title (h2 inside div_request_card_first) ===
    title = None
    h2 = card.select_one('.div_request_card_first h2')
    if h2:
        title = h2.get_text(strip=True)
    if not title:
        return None

    # === Client name (span after h2 in the flex row) ===
    client_name = None
    first_div = card.select_one('.div_request_card_first')
    if first_div:
        # The client name span is at the same level as h2
        for span in first_div.select('span'):
            text = span.get_text(strip=True)
            if text and len(text) < 20 and '前' not in text:
                client_name = text
                break

    # === Location (img[alt="地區"] followed by text) ===
    city, district = None, None
    loc_img = card.select_one('img[alt="地區"]')
    if loc_img:
        # Text is the next sibling or in the parent div
        parent = loc_img.parent
        if parent:
            loc_text = parent.get_text(strip=True)
            if loc_text:
                city, district = parse_location(loc_text)

    # === Budget (img[alt="金額"] followed by text) ===
    budget = None
    budget_img = card.select_one('img[alt="金額"]')
    if budget_img:
        parent = budget_img.parent
        if parent:
            budget = parent.get_text(strip=True)

    # === Time ("XX分鐘前" in div_request_card_first) ===
    posted_at = None
    if first_div:
        for div in first_div.select('div'):
            text = div.get_text(strip=True)
            if re.search(r'(分鐘前|小時前|天前|\d{4}/\d)', text) and len(text) < 30:
                posted_at = parse_relative_time(text)
                break

    # === Description (spans inside div_request_card_second) ===
    description = None
    second_div = card.select_one('.div_request_card_second')
    if second_div:
        spans = second_div.select('span')
        if spans:
            desc_parts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True)]
            description = ' '.join(desc_parts)[:500] if desc_parts else None

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
