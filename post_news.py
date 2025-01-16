import sys
import os
import feedparser
import requests
import yaml
from datetime import datetime, timedelta, timezone

# -----------------------
# グローバル定数・設定
# -----------------------
POSTED_LINKS_FILE = "posted_links.yaml"
JST = timezone(timedelta(hours=9))  # 日本時間 (UTC+9)
CHUNK_SIZE = 5  # 1回の投稿あたりの最大記事数

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
FORUM_CHANNEL_ID = os.getenv("FORUM_CHANNEL_ID")

# -----------------------
# posted_links.yaml 管理
# -----------------------
def load_posted_links():
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_posted_links(all_posted_links):
    with open(POSTED_LINKS_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(all_posted_links, f, allow_unicode=True, default_flow_style=False)

def clean_old_links(all_posted_links, expiration_days):
    now = datetime.now(JST)
    cutoff_time = now - timedelta(days=expiration_days)
    for genre, links in all_posted_links.items():
        all_posted_links[genre] = [
            link for link in links
            if datetime.strptime(link["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST) > cutoff_time
        ]

# -----------------------
# RSS 日付パース系
# -----------------------
def parse_date(entry, field):
    if field + "_parsed" in entry:
        return datetime(*entry[field + "_parsed"][:6])
    if field in entry:
        try:
            return datetime.strptime(entry[field], "%a, %d %b %Y %H:%M:%S %Z")
        except ValueError:
            pass
    return None

def get_entry_date(entry):
    date_fields = ["published", "updated", "dc:date", "pubDate", "created"]
    for field in date_fields:
        date = parse_date(entry, field)
        if date:
            return date
    return None

# -----------------------
# Discord API ユーティリティ
# -----------------------
def get_guild_active_threads():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/threads/active"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("threads", [])
    else:
        print(f"[ERROR] アクティブスレッドの取得に失敗: {response.status_code}, {response.text}")
        sys.exit(1)

def get_channel_archived_threads(archived_type):
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads/archived/{archived_type}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("threads", [])
    else:
        print(f"[ERROR] {archived_type} アーカイブスレッドの取得に失敗: {response.status_code}, {response.text}")
        sys.exit(1)

def filter_threads_by_parent_id(threads, parent_id):
    return [thread for thread in threads if thread.get("parent_id") == parent_id]

def find_existing_thread(category_name):
    active_threads = filter_threads_by_parent_id(get_guild_active_threads(), FORUM_CHANNEL_ID)
    public_archived_threads = get_channel_archived_threads("public")
    private_archived_threads = get_channel_archived_threads("private")
    all_threads = active_threads + public_archived_threads + private_archived_threads

    for thread in all_threads:
        if thread["name"] == category_name:
            return thread
    return None

def unarchive_thread(thread_id):
    url = f"https://discord.com/api/v10/channels/{thread_id}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "archived": False
    }
    response = requests.patch(url, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"[INFO] スレッド {thread_id} をアクティブに戻しました。")
    else:
        print(f"[ERROR] スレッドのアクティブ化に失敗: {response.status_code}, {response.text}")
        sys.exit(1)

def create_thread(category_name, content):
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads"
    payload = {
        "name": category_name,
        "auto_archive_duration": 1440,
        "type": 11,
        "message": {
            "content": content
        }
    }
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        thread_info = response.json()
        print(f"[INFO] スレッド '{category_name}' を作成しました (ID: {thread_info['id']})")
        return thread_info["id"]
    else:
        print(f"[ERROR] スレッド作成に失敗: {response.status_code}, {response.text}")
        sys.exit(1)

def post_message(thread_id, content):
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    payload = {
        "content": content
    }
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"[INFO] メッセージ投稿成功: スレッドID={thread_id}")
        return True
    else:
        print(f"[ERROR] メッセージ投稿に失敗: {response.status_code}, {response.text}")
        sys.exit(1)

def create_or_reply_thread(category_name, content):
    existing_thread = find_existing_thread(category_name)
    if existing_thread:
        thread_id = existing_thread["id"]
        if existing_thread.get("archived", False):
            unarchive_thread(thread_id)
        return post_message(thread_id, content)
    else:
        created_thread_id = create_thread(category_name, content)
        return created_thread_id is not None

# -----------------------
# メイン処理
# -----------------------
def main():
    # 設定ファイルを読み込む
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    expiration_days = config.get("expiration_days", 3)
    max_entries = config.get("max_entries", 10)

    all_posted_links = load_posted_links()

    # config.yaml に存在しないカテゴリを削除
    valid_categories = set(config["genres"].keys())
    all_posted_links = {genre: links for genre, links in all_posted_links.items() if genre in valid_categories}

    # 古いリンクを削除
    clean_old_links(all_posted_links, expiration_days)

    # 更新された posted_links.yaml を保存
    save_posted_links(all_posted_links)

    days_of_week = ["日", "月", "火", "水", "木", "金", "土"]

    for genre, data in config["genres"].items():
        rss_feeds = data["rss_feeds"]

        if genre not in all_posted_links:
            all_posted_links[genre] = []
        posted_links = {link["link"] for link in all_posted_links[genre]}

        all_entries = []
        for rss_url in rss_feeds:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                if entry.link not in posted_links:
                    entry_date = get_entry_date(entry)
                    if entry_date:
                        all_entries.append({
                            "title": entry.title,
                            "link": entry.link,
                            "published": entry_date
                        })

        latest_entries = sorted(all_entries, key=lambda x: x["published"], reverse=True)[:max_entries]

        header_added = False
        for i in range(0, len(latest_entries), CHUNK_SIZE):
            chunk = latest_entries[i:i + CHUNK_SIZE]

            content = ""
            if not header_added:
                now = datetime.now(JST)
                current_time = f"{now.month}月{now.day}日({days_of_week[now.weekday()]}) {now.hour}時"
                content += f"**{current_time} 最新ニュース（{genre}）**\n\n"
                header_added = True

            new_links = []
            for entry in chunk:
                content += f"<{entry['link']}>\n"
                new_links.append({
                    "link": entry["link"],
                    "timestamp": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                })

            if chunk:
                success = create_or_reply_thread(genre, content)
                if success:
                    all_posted_links[genre].extend(new_links)
                    save_posted_links(all_posted_links)
                else:
                    # 「投稿に失敗したら即終了」パターン
                    print(f"[ERROR] スレッドへの投稿に失敗: ジャンル={genre}")
                    sys.exit(1)

if __name__ == "__main__":
    main()
