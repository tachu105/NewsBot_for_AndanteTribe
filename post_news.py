import feedparser
import requests
import yaml
import os
from datetime import datetime, timedelta, timezone

POSTED_LINKS_FILE = "posted_links.yaml"
JST = timezone(timedelta(hours=9))  # 日本時間 (UTC+9)
CHUNK_SIZE = 5  # 1回の投稿あたりの最大記事数

def load_posted_links():
    """過去に投稿済みのリンクをファイルから読み込む"""
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "r") as f:
            return yaml.safe_load(f) or {}  # 空ファイルの場合は空辞書を返す
    return {}  # ファイルが存在しない場合は空の辞書を返す

def save_posted_links(all_posted_links):
    """投稿済みのリンクをファイルに保存する（YAML形式）"""
    with open(POSTED_LINKS_FILE, "w") as f:
        yaml.safe_dump(all_posted_links, f, allow_unicode=True, default_flow_style=False)

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

def clean_old_links(all_posted_links, expiration_days):
    """指定された日数以上前のリンクを削除する"""
    now = datetime.now(JST)
    cutoff_time = now - timedelta(days=expiration_days)
    for genre, links in all_posted_links.items():
        # 各リンクのタイムスタンプを確認し、古いものを除外
        all_posted_links[genre] = [
            link for link in links if datetime.strptime(link["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST) > cutoff_time
        ]

# 設定ファイルを読み込む
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# グローバル設定を読み込み
expiration_days = config.get("expiration_days", 3)  # デフォルトは3日
max_entries = config.get("max_entries", 10)  # デフォルトは10件

# 全カテゴリの投稿済みリンクをロード
all_posted_links = load_posted_links()

# config.yaml に存在しないカテゴリを削除
valid_categories = set(config["genres"].keys())
all_posted_links = {genre: links for genre, links in all_posted_links.items() if genre in valid_categories}

# 古いリンクを削除
clean_old_links(all_posted_links, expiration_days)

# 更新された posted_links.yaml を保存
save_posted_links(all_posted_links)

for genre, data in config["genres"].items():
    webhook_url = data["webhook_url"]
    rss_feeds = data["rss_feeds"]
    
    # 特定のカテゴリの投稿済みリンクを取得（存在しない場合は空のリストを作成）
    if genre not in all_posted_links:
        all_posted_links[genre] = []  # 新しいカテゴリの場合は空リストを初期化
    posted_links = {link["link"] for link in all_posted_links[genre]}  # セットに変換して重複確認を効率化
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

    # 日時順にソートして最新 N 件を取得
    latest_entries = sorted(all_entries, key=lambda x: x["published"], reverse=True)[:max_entries]

    # ヘッダーを付けるかどうかを制御するフラグ
    header_added = False

    # 日本語の曜日リスト
    days_of_week = ["日", "月", "火", "水", "木", "金", "土"]

    # 5件ずつに分割して投稿
    for i in range(0, len(latest_entries), CHUNK_SIZE):
        chunk = latest_entries[i:i + CHUNK_SIZE]
        
        # ヘッダーは最初の投稿にのみ付ける
        content = ""
        if not header_added:
            # 日本時間の現在時刻を取得してフォーマット
            now = datetime.now(JST)
            current_time = f"{now.month}月{now.day}日({days_of_week[now.weekday()]}) {now.hour}時"
            content += f"**{current_time} 最新ニュース（{genre}）**\n\n"
            header_added = True

        new_links = []  # 新しく投稿したリンクを保持
        for entry in chunk:
            content += f"<{entry['link']}>\n"
            new_links
