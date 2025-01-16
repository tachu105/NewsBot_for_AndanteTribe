import requests
import os

# Discord Bot Token (環境変数から取得)
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN が環境変数に設定されていません")

# フォーラムチャンネルID（Discordアプリで取得）
FORUM_CHANNEL_ID = "1329352606954426432"  # フォーラムチャンネルIDを入力してください

# カテゴリ名と投稿内容
categories = {
    "ゲーム": "ゲームに関する最新ニュースはこちら！",
    "テクノロジー": "テクノロジーに関する最新ニュースはこちら！",
}

def get_forum_threads():
    """フォーラム内のアクティブおよびアーカイブ済みスレッドを取得"""
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # アクティブスレッドを取得
    active_url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads/active"
    print("--- アクティブスレッド一覧を取得中 ---")
    active_response = requests.get(active_url, headers=headers)
    print(f"アクティブレスポンスコード: {active_response.status_code}")
    print(f"アクティブレスポンス内容: {active_response.text}")

    active_threads = []
    if active_response.status_code == 200:
        active_threads = active_response.json().get("threads", [])

    # アーカイブ済みスレッドを取得
    archived_url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads/archived/public"
    print("--- アーカイブ済みスレッド一覧を取得中 ---")
    archived_response = requests.get(archived_url, headers=headers)
    print(f"アーカイブレスポンスコード: {archived_response.status_code}")
    print(f"アーカイブレスポンス内容: {archived_response.text}")

    archived_threads = []
    if archived_response.status_code == 200:
        archived_threads = archived_response.json().get("threads", [])

    # アクティブ + アーカイブ済みスレッドを結合
    all_threads = active_threads + archived_threads
    print(f"取得したスレッド数: {len(all_threads)}")
    for thread in all_threads:
        print(f"スレッド名: {thread.get('name')}, ID: {thread.get('id')}, 作成日: {thread.get('timestamp', '不明')}")

    return all_threads

def create_or_reply_thread(category_name, content):
    """同名のスレッドがあれば返信し、なければ新しいスレッドを作成する"""
    threads = get_forum_threads()

    # 同名スレッドを検索
    for thread in threads:
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
print(f"フォーラムチャンネルID: {FORUM_CHANNEL_ID}")
print("--- デバッグ情報終了 ---")

# カテゴリごとにスレッドを作成または返信
for category, content in categories.items():
    create_or_reply_thread(category, content)
