import requests
import os

# Discord Bot Token（Discord Developer Portal で取得）
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# フォーラムチャンネルID（Discordアプリで取得）
FORUM_CHANNEL_ID = "1329352606954426432"  # フォーラムチャンネルIDを入力

# カテゴリ名と投稿内容
categories = {
    "ゲーム": "ゲームに関する最新ニュースはこちら！",
    "テクノロジー": "テクノロジーに関する最新ニュースはこちら！",
}

def create_thread(category_name, content):
    """フォーラム内で新しいスレッドを作成し、投稿する"""
    # スレッド作成用エンドポイント
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads"

    # スレッド作成のペイロード
    payload = {
        "name": category_name,  # スレッド名にカテゴリ名を使用
        "auto_archive_duration": 1440  # スレッドの自動アーカイブ期間（分）。ここでは24時間
    }

    # ヘッダー（認証情報を含む）
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"スレッド '{category_name}' を作成中...")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:  # スレッド作成成功
        thread_id = response.json()["id"]
        print(f"スレッド '{category_name}' が作成されました (ID: {thread_id})")
        post_message(thread_id, content)
    else:
        print(f"スレッド作成に失敗しました: {response.status_code}, {response.json()}")

def post_message(thread_id, content):
    """スレッド内にメッセージを投稿する"""
    url = f"https://discord.com/api/v10/channels/{thread_id}/messages"

    payload = {
        "content": content  # 投稿内容
    }

    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"スレッド (ID: {thread_id}) にメッセージを投稿中...")
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 or response.status_code == 201:
        print(f"メッセージがスレッド (ID: {thread_id}) に投稿されました")
    else:
        print(f"メッセージ投稿に失敗しました: {response.status_code}, {response.json()}")

# カテゴリごとにスレッドを作成して投稿
for category, content in categories.items():
    create_thread(category, content)
