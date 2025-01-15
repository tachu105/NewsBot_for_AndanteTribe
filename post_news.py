import feedparser
import requests
import json
import os
from datetime import datetime

POSTED_LINKS_FILE = "posted_links.json"

def load_posted_links():
    """過去に投稿済みのリンクをファイルから読み込む"""
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "r") as f:
            return json.load(f)
    return {}  # ファイルが存在しない場合は空の辞書を返す

def save_posted_links(all_posted_links):
    """投稿済みのリンクをファイルに保存する（カテゴリごとに分けて1ファイルに保存）"""
    with open(POSTED_LINKS_FILE, "w") as f:
        json.dump(all_posted_links, f, indent=4)  # indent=4 で整形して保存

def parse_date(entry, field):
    """指定されたフィールドの日付をパースする"""
    if field + "_parsed" in entry:
        return datetime(*entry[field + "_parsed"][:6])
    if field in entry:
        try:
            return datetime.strptime(entry[field], "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            pass
    return None

def get_entry_date(entry):
    """エントリから最適な日付を取得する"""
    date_fields = ["published", "updated", "dc:date", "pubDate", "created"]
    for field in date_fields:
        date = parse_date(entry, field)
        if date:
            return date
    return None

# 設定ファイルを読み込む
with open("config.json", "r") as f:
    config = json.load(f)

# 全カテゴリの投稿済みリンクをロード
all_posted_links = load_posted_links()

for genre, data in config["genres"].items():
    webhook_url = data["webhook_url"]
    rss_feeds = data["rss_feeds"]
    
    # 特定のカテゴリの投稿済みリンクを取得（存在しない場合は空のリストを作成）
    if genre not in all_posted_links:
        all_posted_links[genre] = []  # 新しいカテゴリの場合は空リストを初期化
    posted_links = set(all_posted_links[genre])  # セットに変換して重複確認を効率化
    all_entries = []

    for rss_url in rss_feeds:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            if entry.link not in posted_links:  # このカテゴリのリンクだけで重複確認
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
    new_links = set()  # 新しく投稿したリンクを保持
    for entry in latest_entries:
        content += f"<{entry['link']}>\n"
        new_links.add(entry["link"])  # 新しいリンクを追加

    if webhook_url and new_links:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code == 204:
            print(f"ニュースをDiscordに投稿しました: {genre}")
            # 投稿が成功した場合のみ、投稿済みリンクを保存
            posted_links.update(new_links)
            all_posted_links[genre] = list(posted_links)  # 辞書に更新内容を反映
            save_posted_links(all_posted_links)
        else:
            print(f"投稿に失敗しました: {response.status_code}")
    else:
        print(f"Webhook URLが設定されていないか、新しい記事がありません: {genre}")
