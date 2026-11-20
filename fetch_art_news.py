
import json
import re
import html
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

SOURCES = [
    {
        "name": "Music Nation",
        "url": "https://www.musicnation.me/news/category/music-news/",
        "host": "www.musicnation.me"
    },
    {
        "name": "في الفن",
        "url": "https://www.filfan.com/sections/14",
        "host": "www.filfan.com"
    }
]

# كلمات تدل على خبر موسيقي حقيقي
MUSIC_WORDS = [
    "أغنية", "اغنية", "أغاني", "اغاني",
    "ألبوم", "البوم", "ألبومات", "البومات",
    "ميني ألبوم", "كليب", "فيديو كليب",
    "حفلة", "حفل", "حفلات",
    "يحيي", "تحيي", "يحيى حفلا",
    "مهرجان", "جولة غنائية",
    "دويتو", "ديو", "تعاون غنائي",
    "إصدار غنائي", "طرح أغنية", "يطرح أغنية",
    "تطرح أغنية", "أطلق أغنية", "أطلقت أغنية",
    "أطلق ألبوم", "أطلقت ألبوم",
    "أغنيته الجديدة", "أغنيتها الجديدة",
    "أغنيته", "أغنيتها",
    "ألبومه الجديد", "ألبومها الجديد",
    "ألبوم جديد", "أغنية جديدة",
    "أغنية جديدة", "عمل غنائي"
]

# كلمات تستبعد الأخبار غير الموسيقية
BLOCK_WORDS = [
    "مسلسل", "مسلسلات", "فيلم", "أفلام",
    "سينما", "دراما", "ممثل", "ممثلة",
    "برنامج", "طبخ", "زواج", "خطوبة",
    "وفاة", "العناية المركزة", "وعكة صحية",
    "تصريح صادم", "خلاف", "أزمة عائلية",
    "موضة", "فستان", "إطلالة",
    "سرقة", "سياسة", "انتخابات",
    "مباراة", "كرة القدم", "رياضة"
]

# عناوين عامة لا تمثل خبراً
GENERIC_TITLES = {
    "فيديو", "فيديوهات", "ألبوم", "ألبومات",
    "أخبار", "الرئيسية", "المزيد", "مشاهدة",
    "موسيقى", "حفلات", "أغاني", "أخبار فنية",
    "أخبار الموسيقى", "كل الأخبار"
}


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
                self.current = {
                    "href": href,
                    "text": ""
                }

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.links.append(self.current)
            self.current = None


def clean_text(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\n\r-–—|:")


def is_music_story(title):
    title = clean_text(title)

    if len(title) < 22:
        return False

    if title in GENERIC_TITLES:
        return False

    # يجب أن يحتوي العنوان على أحرف عربية
    if not re.search(r"[\u0600-\u06FF]", title):
        return False

    # استبعاد الأخبار غير الموسيقية
    if any(word in title for word in BLOCK_WORDS):
        return False

    # قبول الخبر إذا كان يتحدث عن نشاط موسيقي واضح
    if any(word in title for word in MUSIC_WORDS):
        return True

    return False


def is_article_url(url, source):
    parsed = urlparse(url)

    if parsed.netloc.lower() != source["host"]:
        return False

    path = parsed.path.strip("/").lower()

    if not path:
        return False

    blocked_paths = [
        "category",
        "categories",
        "tag",
        "tags",
        "sections",
        "section",
        "author",
        "search"
    ]

    if any(part in path.split("/") for part in blocked_paths):
        return False

    # منع رابط الصفحة الرئيسية ورابط القسم نفسه
    if url.rstrip("/") == source["url"].rstrip("/"):
        return False

    return True


def fetch_source(source):
    request = urllib.request.Request(
        source["url"],
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; Radio3aHawak/1.0)"
        }
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

        full_url = urljoin(source["url"], href)

        if not full_url.startswith("https://"):
            continue

        if not is_article_url(full_url, source):
            continue

        found[full_url] = {
            "title": title,
            "title_ar": title,
            "link": full_url,
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

            print(
                f'{source["name"]}: '
                f'{len(items)} أخبار موسيقية'
            )

        except Exception as error:
            message = f'{source["name"]}: {error}'
            errors.append(message)
            print("ERROR:", message)

    unique = {}

    for item in all_news:
        unique[item["link"]] = item

    news = list(unique.values())

    news.sort(
        key=lambda item: item["date"],
        reverse=True
    )

    output = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "count": min(len(news), 60),
        "news": news[:60],
        "errors": errors
    }

    with open("art-news.json", "w", encoding="utf-8") as file:
        json.dump(
            output,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("--------------------------------")
    print("راديو ع هواك - تحديث الأخبار")
    print("--------------------------------")
    print(f'عدد الأخبار المحفوظة: {len(output["news"])}')

    if errors:
        print("أخطاء المصادر:")
        for error in errors:
            print(error)

    if not news:
        print("لم يتم العثور على أخبار موسيقية في هذه الجولة.")


if __name__ == "__main__":
    main()
