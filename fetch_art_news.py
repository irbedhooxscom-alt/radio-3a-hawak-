
import json
import re
import html
import urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone

SOURCES = [
    {
        "name": "Music Nation",
        "url": "https://www.musicnation.me/news/category/music-news/",
        "allowed_hosts": ("musicnation.me",)
    },
    {
        "name": "في الفن - موسيقى وحفلات",
        "url": "https://www.filfan.com/sections/14",
        "allowed_hosts": ("filfan.com",)
    }
]

MUSIC_WORDS = [
    "أغنية", "اغنية", "أغاني", "اغاني", "يطرح", "تطرح", "طرح",
    "ألبوم", "البوم", "ميني ألبوم", "كليب", "فيديو كليب",
    "حفلة", "حفل", "حفلات", "يحيي", "تحيي", "مهرجان",
    "جولة غنائية", "دويتو", "ديو", "تعاون غنائي", "إصدار",
    "إطلاق", "منفردة", "جديدة", "جديد", "الغنائي", "الغنائية",
    "الموسيقية"
]

BLOCK_WORDS = [
    "مسلسل", "مسلسلات", "فيلم", "أفلام", "سينما", "دراما",
    "ممثل", "ممثلة", "برنامج", "طبخ", "زواج", "خطوبة",
    "وفاة", "العناية المركزة", "وعكة صحية", "تصريح صادم",
    "خلاف", "أزمة عائلية", "موضة", "فستان", "إطلالة",
    "سرقة", "سياسة", "انتخابات"
]

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs = dict(attrs)
            href = attrs.get("href", "")
            if href:
                self.current = {"href": href, "text": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None

def clean_text(value):
    value = html.unescape(value or "")
    return re.sub(r"\s+", " ", value).strip()

def is_music_story(title):
    if not re.search(r"[\u0600-\u06FF]", title):
        return False
    if any(word in title for word in BLOCK_WORDS):
        return False
    return any(word in title for word in MUSIC_WORDS)

def fetch_source(source):
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "Mozilla/5.0 (compatible; Radio3aHawak/1.0)"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8", errors="replace")

    parser = LinkParser()
    parser.feed(page)
    found = {}

    for entry in parser.links:
        title = clean_text(entry["text"])
        href = entry["href"].strip()
        if not title or not is_music_story(title):
            continue

        if href.startswith("/"):
            href = "https://www." + source["allowed_hosts"][0] + href
        elif href.startswith("//"):
            href = "https:" + href

        if not href.startswith("http"):
            continue
        if not any(host in href for host in source["allowed_hosts"]):
            continue
        if href.rstrip("/") == source["url"].rstrip("/"):
            continue

        found[href] = {
            "title": title,
            "title_ar": title,
            "link": href,
            "description": "",
            "source": source["name"],
            "language": "ar",
            "date": datetime.now(timezone.utc).isoformat()
        }

    return list(found.values())

def main():
    all_news = []
    errors = []

    for source in SOURCES:
        try:
            items = fetch_source(source)
            all_news.extend(items)
            print(f'{source["name"]}: {len(items)} أخبار موسيقية')
        except Exception as error:
            message = f'{source["name"]}: {error}'
            errors.append(message)
            print("ERROR:", message)

    unique = {}
    for item in all_news:
        unique[item["link"]] = item

    news = list(unique.values())
    news.sort(key=lambda item: item["date"], reverse=True)

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": len(news),
        "news": news[:60],
        "errors": errors
    }

    with open("art-news.json", "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=2)

    print(f'تم حفظ {len(output["news"])} خبرًا عن الأغاني والألبومات والحفلات')

    if not news:
        raise SystemExit("لم يتم العثور على أخبار موسيقية. راجع المصادر أو الكلمات المفتاحية.")

if __name__ == "__main__":
    main()
