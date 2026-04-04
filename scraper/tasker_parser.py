"""Parse Tasker.com.tw job listings from SSR NUXT data payload."""

import re
import json
from datetime import datetime, timedelta, timezone

TW_TZ = timezone(timedelta(hours=8))

# Map Tasker top-level category numbers to our category slugs
CATEGORY_MAP = {
    110: 'tasker_ai',          # AI應用
    102: 'tasker_design',      # 商業設計
    103: 'tasker_marketing',   # 行銷企劃
    104: 'tasker_it',          # 資訊工程
    105: 'tasker_writing',     # 文字創作
    106: 'tasker_video',       # 影音製作
    107: 'tasker_translation', # 翻譯語言
    108: 'tasker_accounting',  # 會計記帳
    109: 'tasker_lifestyle',   # 生活服務
}


def parse_relative_time_tasker(text: str) -> str | None:
    """Convert Tasker time formats to ISO timestamp.
    Formats: '11小時', '前天', '2026/04/02', '24分鐘'
    """
    now = datetime.now(TW_TZ)
    text = text.strip()

    m = re.search(r'(\d+)\s*分鐘', text)
    if m:
        return (now - timedelta(minutes=int(m.group(1)))).isoformat()

    m = re.search(r'(\d+)\s*小時', text)
    if m:
        return (now - timedelta(hours=int(m.group(1)))).isoformat()

    if '前天' in text:
        return (now - timedelta(days=2)).isoformat()

    if '昨天' in text:
        return (now - timedelta(days=1)).isoformat()

    m = re.search(r'(\d+)\s*天前', text)
    if m:
        return (now - timedelta(days=int(m.group(1)))).isoformat()

    m = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', text)
    if m:
        dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=TW_TZ)
        return dt.isoformat()

    return None


def extract_nuxt_data(html: str) -> list | None:
    """Extract the __NUXT_DATA__ JSON array from page HTML."""
    m = re.search(r'id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def resolve_value(raw: list, idx):
    """Resolve a NUXT data reference. If idx is an int pointing to another value, follow it."""
    if isinstance(idx, int) and 0 <= idx < len(raw):
        val = raw[idx]
        if isinstance(val, (str, int, float, bool)) or val is None:
            return val
        if isinstance(val, list):
            return [resolve_value(raw, i) for i in val]
        return val
    return idx


def parse_tasker_page(html: str) -> list[dict]:
    """Parse Tasker /cases/top page and return job dicts."""
    raw = extract_nuxt_data(html)
    if not raw:
        print("  [tasker_parser] No NUXT data found")
        return []

    results = []

    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            continue
        # Job listings have tk_no, title, content, budget, loc
        if 'tk_no' not in item or 'title' not in item or 'content' not in item:
            continue

        try:
            job = parse_tasker_job(raw, item)
            if job:
                results.append(job)
        except Exception as e:
            print(f"  [tasker_parser] Error parsing job: {e}")
            continue

    return results


def parse_tasker_job(raw: list, item: dict) -> dict | None:
    """Parse a single Tasker job from NUXT data."""
    tk_no = resolve_value(raw, item.get('tk_no'))
    title = resolve_value(raw, item.get('title'))
    content = resolve_value(raw, item.get('content'))
    loc = resolve_value(raw, item.get('loc'))
    updated_at = resolve_value(raw, item.get('updated_at'))
    min_bid = resolve_value(raw, item.get('min_bid_quota'))

    if not tk_no or not title:
        return None

    # Build job URL
    job_url = f"https://www.tasker.com.tw/cases/{tk_no}"

    # Parse location
    city = None
    district = None
    if loc and isinstance(loc, str) and loc != '可遠端':
        parts = loc.split()
        city = parts[0] if parts else loc
        district = parts[1] if len(parts) > 1 else None
    elif loc == '可遠端':
        city = '遠端'

    # Parse time
    posted_at = None
    if updated_at and isinstance(updated_at, str):
        posted_at = parse_relative_time_tasker(updated_at)

    # Budget — NUXT stores as dict ref like {'text': <idx>} → {'text': '$10,000'}
    budget = None
    budget_val = resolve_value(raw, item.get('budget'))
    if isinstance(budget_val, dict):
        # Resolve nested references in the dict
        budget_text = budget_val.get('text')
        if budget_text is not None:
            resolved_text = resolve_value(raw, budget_text)
            if isinstance(resolved_text, str) and resolved_text:
                budget = resolved_text
        if not budget:
            bmin = resolve_value(raw, budget_val.get('min', budget_val.get('budget_min')))
            bmax = resolve_value(raw, budget_val.get('max', budget_val.get('budget_max')))
            if bmin and bmax:
                budget = f"${bmin:,}-{bmax:,}" if isinstance(bmin, int) else f"${bmin}-{bmax}"
            elif bmin:
                budget = f"${bmin:,}+" if isinstance(bmin, int) else f"${bmin}+"
    elif isinstance(budget_val, (int, float)) and budget_val > 0:
        budget = f"${int(budget_val):,}"
    elif isinstance(budget_val, str) and budget_val:
        budget = budget_val

    if min_bid and not budget:
        budget = f"最低報價 ${int(min_bid):,}" if isinstance(min_bid, int) else str(min_bid)

    # Category — match from service_tags text
    category = 'tasker_other'
    service_tags = item.get('service_tags')
    if service_tags is not None:
        resolved_tags = resolve_value(raw, service_tags)
        if isinstance(resolved_tags, list):
            for tag in resolved_tags:
                tag_text = resolve_value(raw, tag) if isinstance(tag, int) and tag < len(raw) else tag
                if isinstance(tag_text, str):
                    cat = map_tag_to_category(tag_text)
                    if cat:
                        category = cat
                        break

    # Description
    description = content[:500] if content else None

    return {
        "job_url": job_url,
        "title": title,
        "category": category,
        "source": "tasker",
        "city": city,
        "district": district,
        "posted_at": posted_at,
        "description": description,
        "budget": budget,
        "client_name": None,  # Tasker doesn't show client names
    }


TAG_CATEGORY_MAP = {
    # Design 商業設計
    'tasker_design': [
        '平面設計', '視覺設計', 'Logo設計', '商標設計', '名片設計', '包裝設計',
        '信封設計', '美編設計', '品牌設計', '品牌識別', '排版設計', '簡報設計',
        '插畫設計', '漫畫設計', '產品設計', '文宣品設計', '主視覺設計',
        '海報設計', 'DM設計', '封面設計', '印刷設計', 'UI設計', 'UX設計',
    ],
    # Marketing 行銷企劃
    'tasker_marketing': [
        '行銷企劃', '活動企劃', '廣告代操', '社群代操', 'FB粉專', 'FB行銷',
        'SEO', '數位行銷', '網路行銷', '品牌行銷', '廣告投放', '行銷顧問',
        'FB 行銷', '小編', 'IG行銷',
    ],
    # IT & Programming 資訊工程
    'tasker_it': [
        '網站架設', '網頁設計', 'APP開發', '程式設計', '軟體開發', '系統開發',
        '網路應用程式', '資料庫', '前端', '後端', '爬蟲', 'API',
        '電子電路設計', '網路拉線', 'IOT', '物聯網', 'wifi', '線上簽核',
        '電話總機', '電商平台',
    ],
    # Video & Audio 影音製作
    'tasker_video': [
        '影片製作', '影片剪輯', '影片後製', '短影音', '動畫製作', '動態設計',
        '音效', '配音', '錄音', '影片行銷', '企業影片', 'MV拍攝',
        '影片/音效後製剪輯', '簡報製作',
    ],
    # Writing 文字創作
    'tasker_writing': [
        '文案', '寫作', '編輯', '校對', '部落格', '新聞稿', '文章撰寫',
        '寫作服務', '劇本', '企劃書',
    ],
    # Translation 翻譯語言
    'tasker_translation': [
        '翻譯', '口譯', '英文翻譯', '日文翻譯', '韓文翻譯', '中翻英',
        '英翻中', '同步口譯', '現場口譯', '英文口譯', '現場同步口譯',
    ],
    # Accounting 會計記帳
    'tasker_accounting': [
        '會計', '記帳', '報稅', '稅務', '薪資', '公司登記', '行號登記',
        '記帳服務', '會計報稅', '稅務簽證', '稅務規劃', '公司所得申報',
        '薪資外包', '公司登記申請',
    ],
    # Lifestyle 生活服務
    'tasker_lifestyle': [
        '清潔', '搬家', '裝修', '油漆', '木工', '水電', '修繕',
        '房屋修繕', '油漆工程', '系統櫃', '圍牆彩繪', '牆壁彩繪',
        '客服', '顧問', '企業管理', '客服諮詢', '企業管理顧問',
        '活動視覺',
    ],
    # AI AI應用
    'tasker_ai': [
        'AI', '人工智慧', '機器學習', 'ChatGPT', '大數據', '自動化',
        'n8n', 'AI Agent', 'AI開發',
    ],
}


def map_tag_to_category(tag_text: str) -> str | None:
    """Map a Tasker service tag string to our category slug."""
    for cat_slug, keywords in TAG_CATEGORY_MAP.items():
        for kw in keywords:
            if kw in tag_text:
                return cat_slug
    return None
