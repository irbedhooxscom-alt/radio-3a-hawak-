
import json
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    {
        "name": "Arabsounds",
        "url": "https://www.arabsounds.net/blog?format=rss",
        "language": "en"
    },
    {
        "name": "NME Music",
        "url": "https://www.nme.com/news/music/feed",
        "language": "en"
    },
    {
        "name": "Variety Music",
        "url": "https://variety.com/v/music/feed/",
        "language": "en"
    }
]

KEYWORDS = [
    "music", "song", "single", "album", "singer", "artist",
    "concert", "tour", "festival", "live", "release",
    "new track", "music video", "performance",
    "أغنية", "اغنية", "ألبوم", "البوم", "مطرب",
    "فنان", "مغني", "حفلة", "حفل", "حفلات",
    "موسيقى", "جولة غنائية", "إصدار", "جديد"
]

def get_text(element, tag):
    node = element.find(tag)
    if node is None:
        return ""
    return (node.text or "").strip()

def is_music_news(title, description):
    text = (title + " " + description).lower()
    return any(word in text for word in KEYWORDS)

def translate_to_arabic(title, language):
    if language == "ar" or re.search(r"[\u0600-\u06FF]", title):
        return title

    params = urllib.parse.urlencode({
        "client": "gtx",
        "sl": "auto",
        "tl": "ar",
        "dt": "t",
        "q": title
    })

    url = "https://translate.googleapis.com/translate_a/single?" + params

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            result = json.loads(response.read().decode("utf-8"))

        translated = "".join(
            part[0] for part in result[0] if part and part[0]
        )

        return translated.strip() or title

    except Exception as error:
        print("Translation error:", error)
        return title

def fetch_feed(feed):
    request = urllib.request.Request(
        feed["url"],
        headers={
            "User-Agent": "Mozilla/5.0 Radio3aHawak/1.0",
            "Accept": "application/rss+xml, application/xml, text/xml"
        }
    )

    with urllib.request.urlopen(request, timeout=25) as response:
        xml_data = response.read()

    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item"):
        title = get_text(item, "title")
        link = get_text(item, "link")
        description = get_text(item, "description")
        pub_date = get_text(item, "pubDate")

        if not title or not link:
            continue

        if not is_music_news(title, description):
            continue

        date_iso = ""

        if pub_date:
            try:
                date_iso = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                date_iso = pub_date

        title_ar = translate_to_arabic(title, feed["language"])
        time.sleep(0.3)

        items.append({
            "title": title,
            "title_ar": title_ar,
            "link": link,
            "description": description,
            "source": feed["name"],
            "language": feed["language"],
            "date": date_iso
        })

    return items

def main():
    all_news = []
    errors = []

    for feed in FEEDS:
        try:
            items = fetch_feed(feed)
            all_news.extend(items)
            print(f'{feed["name"]}: {len(items)} music news')
        except Exception as error:
            message = f'{feed["name"]}: {error}'
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

    print(f'تم حفظ {len(output["news"])} خبر موسيقي')

    if not news:
        raise SystemExit("لم يتم جلب أخبار موسيقية. راجع رسائل ERROR.")

if __name__ == "__main__":
    main()
