
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEEDS = [
    {
        "name": "CNN العربية",
        "url": "https://arabic.cnn.com/rss/cnnarabic_entertainment.rss",
        "language": "ar"
    },
    {
        "name": "Variety - Music",
        "url": "https://variety.com/v/music/feed/",
        "language": "en"
    },
    {
        "name": "Variety - Film",
        "url": "https://variety.com/v/film/feed/",
        "language": "en"
    }
]

def get_text(element, tag):
    node = element.find(tag)
    if node is None:
        return ""
    return (node.text or "").strip()

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

        date_iso = ""

        if pub_date:
            try:
                date_iso = parsedate_to_datetime(pub_date).isoformat()
            except Exception:
                date_iso = pub_date

        items.append({
            "title": title,
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
            print(f"{feed['name']}: {len(items)} أخبار")
        except Exception as error:
            message = f"{feed['name']}: {error}"
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

    print(f"تم حفظ {len(output['news'])} خبرًا في art-news.json")

    if not news:
        raise SystemExit("لم يتم جلب أي خبر. راجع رسائل ERROR أعلاه.")

if __name__ == "__main__":
    main()
