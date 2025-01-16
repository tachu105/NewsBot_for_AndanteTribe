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
    print(f"レスポンスコード: {response.status_code}")
    print(f"レスポンス内容: {response.text}")

    if response.status_code == 200:
        threads = response.json().get("threads", [])
        print(f"取得したスレッド数: {len(threads)}")
        for thread in threads:
            print(f"スレッド名: {thread.get('name')}, 親チャンネルID: {thread.get('parent_id')}, スレッドID: {thread.get('id')}")
        return threads
    else:
        print(f"サーバー全体のアクティブスレッド取得に失敗しました: {response.status_code}, {response.text}")
        return []

def filter_threads_by_parent_id(threads, parent_id):
    """親チャンネルIDでスレッドをフィルタリング"""
    return [thread for thread in threads if thread.get("parent_id") == parent_id]

def create_or_reply_thread(category_name, content):
    """同名のスレッドがあれば返信し、なければ新しいスレッドを作成する"""
    # サーバー全体のアクティブスレッドを取得
    all_threads = get_guild_active_threads()

    # フォーラムチャンネルのスレッドに絞り込む
    forum_threads = filter_threads_by_parent_id(all_threads, FORUM_CHANNEL_ID)

    # 同名スレッドを検索
    for thread in forum_threads:
        if thread["name"] == category_name:
            print(f"既存のスレッド '{category_name}' が見つかりました (ID: {thread['id']})")
            post_message(thread["id"], content)
            return

    # 同名スレッドがなければ新しいスレッドを作成
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

# 環境変数とチャンネルIDのデバッグ
print("--- デバッグ情報 ---")
print(f"トークンの最初の10文字: {DISCORD_BOT_TOKEN[:10]}...")
print(f"サーバーID: {GUILD_ID}")
print(f"フォーラムチャンネルID: {FORUM_CHANNEL_ID}")
print("--- デバッグ情報終了 ---")

# カテゴリごとにスレッドを作成または返信
for category, content in categories.items():
    create_or_reply_thread(category, content)
