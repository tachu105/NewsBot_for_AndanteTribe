import os
import sys
import requests

class DiscordService:
    # ---------------------
    # コンストラクタ
    # ---------------------
    def __init__(self, bot_token, guild_id, forum_channel_id):
        self.bot_token = bot_token
        self.guild_id = guild_id
        self.forum_channel_id = forum_channel_id

    # ---------------------
    # サーバー全体のアクティブスレッドを取得
    # ---------------------
    def get_guild_active_threads(self):
        url = f"https://discord.com/api/v10/guilds/{self.guild_id}/threads/active"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("[INFO] アクティブスレッドの取得に成功")
            return r.json().get("threads", [])
        else:
            print(f"[ERROR] アクティブスレッドの取得に失敗: {r.status_code}, {r.text}")
            sys.exit(1)

    # ---------------------
    # 公開アーカイブスレッドを取得
    # ---------------------
    def get_public_archived_threads(self):
        url = f"https://discord.com/api/v10/channels/{self.forum_channel_id}/threads/archived/public"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            print("[INFO] 公開アーカイブスレッドの取得に成功")
            return r.json().get("threads", [])
        else:
            print(f"[ERROR] 公開アーカイブスレッドの取得に失敗: {r.status_code}, {r.text}")
            sys.exit(1)

    # ---------------------
    # 親チャンネルIDに合致するスレッドをフィルタ
    # ---------------------
    def filter_threads_by_parent_id(self, threads, parent_id):
        return [t for t in threads if t.get("parent_id") == parent_id]

    # ---------------------
    # スレッドのアーカイブ化を解除
    # ---------------------
    def unarchive_thread(self, thread_id):
        url = f"https://discord.com/api/v10/channels/{thread_id}"
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        payload = {"archived": False}
        r = requests.patch(url, headers=headers, json=payload)
        if r.status_code == 200:
            print(f"[INFO] スレッド {thread_id} のアーカイブ解除に成功")
        else:
            print(f"[ERROR] スレッドのアクティブ化に失敗: {r.status_code}, {r.text}")
            sys.exit(1)

    # ---------------------
    # 新しいスレッドを作成して最初のメッセージを投稿
    # ---------------------
    def create_thread(self, category_name, content):
        if not content.strip():
            content = f"スレッド（{category_name}）を新規に自動生成しました。"
        
        url = f"https://discord.com/api/v10/channels/{self.forum_channel_id}/threads"
        payload = {
            "name": category_name,
            "auto_archive_duration": 1440,
            "type": 11,
            "message": {
                "content": content
            }
        }
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 201:
            thread_info = r.json()
            print(f"[INFO] スレッド '{category_name}' を作成 (ID: {thread_info['id']})")
            return thread_info["id"]
        else:
            print(f"[ERROR] スレッド作成に失敗: {r.status_code}, {r.text}")
            sys.exit(1)

    # ---------------------
    # 既存スレッドにメッセージを投稿
    # ---------------------
    def post_message(self, thread_id, content):
        url = f"https://discord.com/api/v10/channels/{thread_id}/messages"
        payload = {"content": content}
        headers = {
            "Authorization": f"Bot {self.bot_token}",
            "Content-Type": "application/json"
        }
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code in [200, 201]:
            print(f"[INFO] メッセージ投稿成功: スレッドID={thread_id}")
            return True
        else:
            print(f"[ERROR] メッセージ投稿に失敗: {r.status_code}, {r.text}")
            sys.exit(1)
