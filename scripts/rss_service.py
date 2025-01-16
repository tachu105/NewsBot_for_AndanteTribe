import feedparser
from datetime import datetime

class RssService:
    # ---------------------
    # コンストラクタ
    # ---------------------
    def __init__(self):
        pass

    # ---------------------
    # RSSを取得し、エントリをまとめて返す
    # ---------------------
    def fetch_rss_entries(self, rss_urls):
        all_entries = []
        for rss_url in rss_urls:
            feed = feedparser.parse(rss_url)
            print(f"[INFO] RSS取得成功: {rss_url} (記事件数: {len(feed.entries)})")

            for entry in feed.entries:
                dt = self.get_entry_date(entry)
                if dt:
                    all_entries.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": dt
                    })
        return all_entries

    # ---------------------
    # エントリから最適な日付を取得
    # ---------------------
    def get_entry_date(self, entry):
        date_fields = ["published", "updated", "dc:date", "pubDate", "created"]
        for field in date_fields:
            dt = self.parse_date(entry, field)
            if dt:
                return dt
        return None

    # ---------------------
    # 指定されたフィールドの日付をパース
    # ---------------------
    def parse_date(self, entry, field):
        if field + "_parsed" in entry:
            return datetime(*entry[field + "_parsed"][:6])
        if field in entry:
            try:
                return datetime.strptime(entry[field], "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                pass
        return None
