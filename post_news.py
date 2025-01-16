import feedparser
import requests
import yaml
import os
from datetime import datetime, timedelta, timezone

POSTED_LINKS_FILE = "posted_links.yaml"
JST = timezone(timedelta(hours=9))  # 日本時間 (UTC+9)
CHUNK_SIZE = 5  # 1回の投稿あたりの最大記事数

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Discord Botのトークン

# ギルドIDとフォーラムチャンネルIDを統一
GUILD_ID = "1329018285811040277"  # サーバーのギルドID
FORUM_CHANNEL_ID = "1329352606954426432"  # フォーラムチャンネルのID

def load_posted_links():
    """過去に投稿済みのリンクをファイルから読み込む"""
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "r") as f:
            return yaml.safe_load(f) or {}  # 空ファイルの場合は空辞書を返す
    return {}

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

def get_guild_active_threads():
    """サーバー全体のアクティブスレッドを取得"""
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/threads/active"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("threads", [])
    else:
        print(f"アクティブスレッドの取得に失敗: {response.status_code}, {response.text}")
        return []

def get_channel_archived_threads(archived_type):
    """特定のチャンネル内のアーカイブスレッドを取得"""
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads/archived/{archived_type}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("threads", [])
    else:
        print(f"{archived_type} アーカイブスレッドの取得に失敗: {response.status_code}, {response.text}")
        return []

def find_existing_thread(category_name):
    """サーバー内のスレッドを検索し、既存スレッドを探す"""
    active_threads = get_guild_active_threads()
    public_archived_threads = get_channel_archived_threads("public")
    private_archived_threads = get_channel_archived_threads("private")

    all_threads = active_threads + public_archived_threads + private_archived_threads
    for thread in all_threads:
        if thread["parent_id"] == FORUM_CHANNEL_ID and thread["name"] == category_name:
            return thread
    return None

def unarchive_thread(thread_id):
    """アーカイブされたスレッドをアクティブに戻す"""
    url = f"https://discord.com/api/v10/channels/{thread_id}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.patch(url, json={"archived": False}, headers=headers)
    if response.status_code == 200:
        print(f"スレッド {thread_id} をアクティブ化しました")
    else:
        print(f"スレッドのアクティブ化に失敗: {response.status_code}, {response.text}")

def create_or_reply_thread(category_name, content):
    """同名のスレッドがあれば返信し、なければ新しいスレッドを作成する"""
    existing_thread = find_existing_thread(category_name)
    if existing_thread:
        if existing_thread.get("archived", False):
            unarchive_thread(existing_thread["id"])
        post_message(existing_thread["id"], content)
    else:
        create_thread(category_name, content)

def create_thread(category_name, content):
    """新しいスレッドを作成"""
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads"
    payload = {
        "name": category_name,
        "auto_archive_duration": 1440,
        "type": 11,
        "message": {"content": content}
    }
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"スレッド '{category_name}' を作成しました")
    else:
        print(f"スレッド作成に失敗: {response.status_code}, {response.text}")

def post_message(thread_id, content):
    """既存スレッドにメッセージを投稿"""
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
    payload = {"content": content}
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"スレッド {thread_id} にメッセージを投稿しました")
    else:
        print(f"メッセージ投稿に失敗: {response.status_code}, {response.text}")

# YAML設定ファイルの読み込み
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

expiration_days = config.get("expiration_days", 3)
max_entries = config.get("max_entries", 10)
all_posted_links = load_posted_links()

for genre, data in config["genres"].items():
    rss_feeds = data["rss_feeds"]
    posted_links = {link["link"] for link in all_posted_links.get(genre, [])}
    entries = []

    for rss_url in rss_feeds:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            if entry.link not in posted_links:
                entry_date = get_entry_date(entry)
                if entry_date:
                    entries.append({"title": entry.title, "link": entry.link, "published": entry_date})

    entries.sort(key=lambda x: x["published"], reverse=True)
    entries = entries[:max_entries]
    for i in range(0, len(entries), CHUNK_SIZE):
        chunk = entries[i:i + CHUNK_SIZE]
        content = "\n".join(f"<{entry['link']}>" for entry in chunk)
        create_or_reply_thread(genre, content)
