import requests
import os

# 環境変数からBotトークンとフォーラムチャンネルIDを取得
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1329018285811040277"  # サーバーIDを入力
FORUM_CHANNEL_ID = "1329352606954426432"  # フォーラムチャンネルIDを入力

# カテゴリ名と投稿内容
categories = {
    "ゲーム": "ゲームに関する最新ニュースはこちら！",
    "テクノロジー": "テクノロジーに関する最新ニュースはこちら！",
}

def get_guild_active_threads():
    """サーバー全体のアクティブスレッドを取得"""
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/threads/active"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print("--- サーバー全体のアクティブスレッドを取得中 ---")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        threads = response.json().get("threads", [])
        print(f"取得したアクティブスレッド数: {len(threads)}")
        return threads
    else:
        print(f"アクティブスレッドの取得に失敗しました: {response.status_code}, {response.text}")
        return []

def get_channel_archived_threads(archived_type):
    """特定のチャンネル内のアーカイブスレッドを取得"""
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads/archived/{archived_type}"
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"--- {archived_type} アーカイブスレッドを取得中 ---")
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        threads = response.json().get("threads", [])
        print(f"取得した {archived_type} アーカイブスレッド数: {len(threads)}")
        return threads
    else:
        print(f"{archived_type} アーカイブスレッドの取得に失敗しました: {response.status_code}, {response.text}")
        return []

def filter_threads_by_parent_id(threads, parent_id):
    """親チャンネルIDでスレッドをフィルタリング"""
    return [thread for thread in threads if thread.get("parent_id") == parent_id]

def find_existing_thread(category_name):
    """すべてのスレッド（アクティブおよびアーカイブ）を検索して一致するスレッドを探す"""
    # サーバー全体のアクティブスレッドを取得
    active_threads = filter_threads_by_parent_id(get_guild_active_threads(), FORUM_CHANNEL_ID)

    # 公開および非公開アーカイブスレッドを取得
    public_archived_threads = get_channel_archived_threads("public")
    private_archived_threads = get_channel_archived_threads("private")

    # すべてのスレッドを統合
    all_threads = active_threads + public_archived_threads + private_archived_threads

    # カテゴリ名に一致するスレッドを検索
    for thread in all_threads:
        if thread["name"] == category_name:
            print(f"既存のスレッドが見つかりました: {thread['name']} (ID: {thread['id']})")
            return thread["id"]

    print(f"カテゴリ '{category_name}' に一致するスレッドは見つかりませんでした")
    return None

def create_or_reply_thread(category_name, content):
    """同名のスレッドがあれば返信し、なければ新しいスレッドを作成する"""
    # 既存のスレッドを検索
    existing_thread_id = find_existing_thread(category_name)

    if existing_thread_id:
        # 既存のスレッドに投稿
        post_message(existing_thread_id, content)
    else:
        # 新しいスレッドを作成
        create_thread(category_name, content)

def create_thread(category_name, content):
    """新しいスレッドを作成"""
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

    print(f"--- 新しいスレッド作成開始: {category_name} ---")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"スレッド '{category_name}' が作成されました")
    else:
        print(f"スレッド作成に失敗しました: {response.status_code}, {response.text}")

def post_message(thread_id, content):
    """既存スレッドにメッセージを投稿"""
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"

    payload = {
        "content": content
    }

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"--- メッセージ投稿開始: スレッドID {thread_id} ---")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        print(f"メッセージがスレッド (ID: {thread_id}) に投稿されました")
    else:
        print(f"メッセージ投稿に失敗しました: {response.status_code}, {response.text}")

# カテゴリごとにスレッドを作成または返信
for category, content in categories.items():
    create_or_reply_thread(category, content)
