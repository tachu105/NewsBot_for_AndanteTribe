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

def create_thread(category_name, content):
    """フォーラム内で新しいスレッドを作成し、投稿する"""
    url = f"https://discord.com/api/v10/channels/{FORUM_CHANNEL_ID}/threads"

    # スレッド作成のペイロード
    payload = {
        "name": category_name,  # スレッド名
        "auto_archive_duration": 1440,  # スレッドの自動アーカイブ期間（分）。ここでは24時間
        "type": 11,  # フォーラムスレッドのタイプ
        "message": {  # スレッド作成時の最初の投稿内容
            "content": content
        }
    }

    # ヘッダー（認証情報を含む）
    headers = {
        "Authorization": f"Bot {DISCORD_BOT_TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"--- スレッド作成開始: {category_name} ---")
    print(f"使用するエンドポイント: {url}")
    print(f"送信ペイロード: {payload}")
    print(f"送信ヘッダー: {headers}")

    response = requests.post(url, json=payload, headers=headers)
    print(f"レスポンスコード: {response.status_code}")
    try:
        print(f"レスポンス内容: {response.json()}")
    except Exception as e:
        print(f"レスポンス内容をJSONとして解析できません: {response.text}, エラー: {e}")

    if response.status_code == 201:  # スレッド作成成功
        thread_id = response.json()["id"]
        print(f"スレッド '{category_name}' が作成されました (ID: {thread_id})")
    else:
        print(f"スレッド作成に失敗しました: {response.status_code}, {response.text}")

# 環境変数とチャンネルIDのデバッグ
print("--- デバッグ情報 ---")
print(f"トークンの最初の10文字: {DISCORD_BOT_TOKEN[:10]}...")
print(f"フォーラムチャンネルID: {FORUM_CHANNEL_ID}")
print("--- デバッグ情報終了 ---")

# カテゴリごとにスレッドを作成して投稿
for category, content in categories.items():
    create_thread(category, content)
