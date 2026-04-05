"""Classify PRO360 job titles into categories using keyword matching."""
from __future__ import annotations

# Keywords are checked in order — first match wins.
# Categories with more specific keywords come first to avoid
# generic terms like "裝修" or "教學" catching everything.
PRO360_CATEGORY_MAP: dict[str, list[str]] = {
    "cleaning": [
        "清潔", "清洗", "打掃", "大掃除", "除霉", "拋光", "打蠟",
        "鍍膜", "洗衣機清", "冷氣清", "水塔清", "床墊清", "地毯清",
        "沙發清", "抽油煙機", "安全座椅清", "玻璃清", "環保工程",
        "烘衣機清", "空氣清淨機清", "熱水器清",
    ],
    "ac_repair": [
        "冷氣維修", "冷氣安裝", "冷氣移機", "冷氣保養", "冷氣拆",
        "暖氣", "空調",
    ],
    "pest_control": [
        "除蟲", "滅鼠", "白蟻", "蟑螂", "蚊蟲", "消毒",
        "驅蟲", "除蟻", "害蟲",
    ],
    # handyman BEFORE renovation — "馬桶裝修" is plumbing, not renovation
    "handyman": [
        "水電", "馬桶", "漏水", "抓漏", "通水管", "管線",
        "插座", "開關", "配電", "電路", "電線", "燈具", "熱水器安裝",
        "瓦斯", "洗臉盆", "水龍頭", "衛浴", "暖風機",
        "鎖匠", "換鎖", "開鎖", "門鎖",
        "洗衣機裝修", "洗衣機安裝",  # appliance install/repair = handyman
    ],
    "renovation": [
        "裝潢", "裝修", "室內設計", "翻新", "拆除", "泥作", "磁磚",
        "天花板", "隔間", "輕隔間", "統包", "系統櫃", "廚具",
        "浴室門", "鋁窗", "鐵窗", "採光罩", "防水工程", "壁癌",
        "油漆", "粉刷", "批土", "木工", "地板", "壁紙",
        "窗簾安裝", "百葉窗", "鐵捲門", "電動門", "門窗",
    ],
    "moving": [
        "搬家", "搬運", "回收", "廢棄物", "載貨", "運輸",
        "回頭車", "代收垃圾", "托運", "吊車",
        "大型家具回收", "傢俱回收",
    ],
    # web_dev BEFORE tutoring — "ChatGPT 教學" is tech, not tutoring
    "web_dev": [
        "網頁", "網站", "APP", "app", "程式", "軟體",
        "ChatGPT", "AI ", "電商", "系統開發",
    ],
    "tutoring": [
        "家教", "教學", "課程", "補習", "伴讀", "陪玩",
        "桌球", "羽球", "游泳", "瑜珈", "書法", "鋼琴",
        "吉他", "歌唱", "舞蹈", "繪畫",
    ],
    "photography": [
        "攝影", "拍攝", "婚攝", "寫真", "錄影", "空拍",
        "商業攝影", "活動攝影", "妝髮", "彩妝", "新秘",
    ],
    "design": [
        "設計", "插畫", "名片", "Logo", "LOGO", "logo",
        "招牌", "大圖輸出", "印刷", "排版", "美編",
    ],
}

# Fallback category when no keywords match
FALLBACK_CATEGORY = "other"


def classify_pro360(title: str, description: str | None = None) -> str:
    """Classify a PRO360 job by its title (and optionally description).

    Checks title first for a quick match. Falls back to description
    if title doesn't match any category.
    """
    # Check title first (most reliable)
    for category, keywords in PRO360_CATEGORY_MAP.items():
        for kw in keywords:
            if kw in title:
                return category

    # Fallback: check description
    if description:
        desc_short = description[:200]
        for category, keywords in PRO360_CATEGORY_MAP.items():
            for kw in keywords:
                if kw in desc_short:
                    return category

    return FALLBACK_CATEGORY
