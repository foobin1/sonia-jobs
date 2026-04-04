"""PRO360 scraper configuration."""

BASE_URL = "https://www.pro360.com.tw"

CATEGORIES = {
    "cleaning":     {"name_zh": "清潔服務", "name_en": "Cleaning",           "path": "/case/subgenre/cleaning"},
    "handyman":     {"name_zh": "水電工程", "name_en": "Plumbing & Electrical", "path": "/case/subgenre/handyman"},
    "moving":       {"name_zh": "搬家回收", "name_en": "Moving",             "path": "/case/subgenre/moving"},
    "tutoring":     {"name_zh": "家教",     "name_en": "Tutoring",           "path": "/case/subgenre/tutoring"},
    "design":       {"name_zh": "平面設計", "name_en": "Graphic Design",     "path": "/case/subgenre/design"},
    "photography":  {"name_zh": "攝影服務", "name_en": "Photography",        "path": "/case/subgenre/photography"},
    "renovation":   {"name_zh": "裝潢設計", "name_en": "Renovation",         "path": "/case/subgenre/renovation"},
    "pest_control": {"name_zh": "消毒除蟲", "name_en": "Pest Control",       "path": "/case/subgenre/pest_control"},
    "ac_repair":    {"name_zh": "冷氣維修", "name_en": "AC Repair",          "path": "/case/subgenre/ac_repair"},
    "web_dev":      {"name_zh": "網頁程式", "name_en": "Web Development",    "path": "/case/subgenre/web_dev"},
}

# Scraper settings
POLL_INTERVAL_MIN = 180   # 3 minutes
POLL_INTERVAL_MAX = 300   # 5 minutes
REQUEST_DELAY_MIN = 3     # seconds between requests
REQUEST_DELAY_MAX = 8

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]
