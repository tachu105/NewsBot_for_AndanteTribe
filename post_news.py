import feedparser
import requests
import json
import os
from datetime import datetime

def get_entry_date(entry):
    """エントリから最適な日付を取得する"""
    date_fields = ["published", "updated", "dc:date", "pubDate", "created"]  # 優先順位で候補を並べる
    for field in date_fields:
        if field in entry:
            return datetime(*entry[field + "_parsed"][:6])  # パースして返す
    return None  # 日付が見つからない場合

# 設定ファイルを読み込む
with open("config.json", "r") as f:
    config = json.load(f)

seen_links = set()

for genre, data in config["genres"].items():
    webhook_url = data["webhook_url"]
    rss_feeds = data["rss_feeds"]
    
    all_entries = []

    for rss_url in rss_feeds:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            if entry.link not in seen_links:
                seen_links.add(entry.link)
                entry_date = get_entry_date(entry)
                if entry_date:
                    all_entries.append({
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry_date
                    })

    # 日時順にソートして最新10件を取得
    latest_entries = sorted(all_entries, key=lambda x: x["published"], reverse=True)[:10]

    content = f"**最新ニュース（{genre.capitalize()}）**\n\n"
    for entry in latest_entries:
        content += f"[_]({entry['link']}) "

    if webhook_url:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code == 204:
            print(f"ニュースをDiscordに投稿しました: {genre}")
        else:
            print(f"投稿に失敗しました: {response.status_code}")
    else:
        print(f"Webhook URLが設定されていません: {genre}")
