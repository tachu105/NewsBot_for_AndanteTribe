import sys
import os
from datetime import datetime, timezone, timedelta

# ---------------------
# 必要なクラスをインポート
# ---------------------
from scripts.config_manager import ConfigManager
from scripts.posted_links_manager import PostedLinksManager
from scripts.rss_service import RssService
from scripts.discord_service import DiscordService

JST = timezone(timedelta(hours=9))  # 日本時間 (UTC+9)
CHUNK_SIZE = 5  # 1回の投稿あたりの最大記事数

class PostNews:
    # ---------------------
    # コンストラクタ
    # ---------------------
    def __init__(self, config_file_path, posted_links_path, bot_token, guild_id, forum_channel_id):
        self.config_manager = ConfigManager(config_file_path)
        self.posted_links_manager = PostedLinksManager(posted_links_path)
        self.rss_service = RssService()
        self.discord_service = DiscordService(bot_token, guild_id, forum_channel_id)

    # ---------------------
    # 既存スレッドを探す
    # ---------------------
    def find_existing_thread(self, category_name):
        active_threads = self.discord_service.get_guild_active_threads()
        active_threads = self.discord_service.filter_threads_by_parent_id(
            active_threads, self.discord_service.forum_channel_id
        )
        public_archived = self.discord_service.get_public_archived_threads()
        public_archived = self.discord_service.filter_threads_by_parent_id(
            public_archived, self.discord_service.forum_channel_id
        )

        all_threads = active_threads + public_archived
        for t in all_threads:
            if t["name"] == category_name:
                print(f"[INFO] 既存スレッド発見: {t['name']} (ID: {t['id']})")
                return t
        print(f"[INFO] カテゴリ '{category_name}' の既存スレッドは見つかりません")
        return None

    # ---------------------
    # 既存 or 新規スレッドに投稿
    # ---------------------
    def create_or_reply_thread(self, category_name, content):
        thread = self.find_existing_thread(category_name)
        if thread:
            thread_id = thread["id"]
            if thread.get("archived", False):
                self.discord_service.unarchive_thread(thread_id)
            return self.discord_service.post_message(thread_id, content)
        else:
            new_id = self.discord_service.create_thread(category_name, content)
            return bool(new_id)

    # ---------------------
    # メイン処理
    # ---------------------
    def run(self):
        # config.yaml の読み込み
        config = self.config_manager.load_config()
        expiration_days = config.get("expiration_days", 3)
        max_entries = config.get("max_entries", 10)

        # posted_links.yaml の読み込み & 古いリンク削除
        all_posted_links = self.posted_links_manager.load()
        valid_categories = set(config["genres"].keys())
        all_posted_links = {
            g: links for g, links in all_posted_links.items() if g in valid_categories
        }
        self.posted_links_manager.clean_old_links(all_posted_links, expiration_days)
        self.posted_links_manager.save(all_posted_links)

        # 日本語の曜日リスト
        days_of_week = ["日", "月", "火", "水", "木", "金", "土"]

        # ジャンルごとに RSS取得 → 投稿
        for genre, data in config["genres"].items():
            if genre not in all_posted_links:
                all_posted_links[genre] = []

            posted_links_set = {item["link"] for item in all_posted_links[genre]}
            rss_urls = data["rss_feeds"]

            # RSS エントリ取得
            all_entries = self.rss_service.fetch_rss_entries(rss_urls)
            # 未投稿のものだけ絞る
            new_entries = [e for e in all_entries if e["link"] not in posted_links_set]

            # 日付順ソート & max_entries 件に絞る
            latest_entries = sorted(new_entries, key=lambda x: x["published"], reverse=True)[:max_entries]

            header_added = False
            for i in range(0, len(latest_entries), CHUNK_SIZE):
                chunk = latest_entries[i:i+CHUNK_SIZE]
                if not chunk:
                    continue

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

                success = self.create_or_reply_thread(genre, content)
                if success:
                    all_posted_links[genre].extend(new_links)
                    self.posted_links_manager.save(all_posted_links)
                else:
                    print(f"[ERROR] スレッド投稿に失敗: genre={genre}")
                    sys.exit(1)


# ---------------------
# スクリプトのエントリポイント
# ---------------------
def main():
    # 環境変数から読み取る例 (もしくは引数で受け取る等)
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    guild_id = os.getenv("GUILD_ID")
    forum_channel_id = os.getenv("FORUM_CHANNEL_ID")

    # datasフォルダのパスを組み立て
    base_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(base_dir, '..', 'datas', 'config.yaml')
    posted_links_path = os.path.join(base_dir, '..', 'datas', 'posted_links.yaml')

    # OOPクラスを初期化して実行
    app = PostNews(
        config_file_path=config_file_path,
        posted_links_path=posted_links_path,
        bot_token=bot_token,
        guild_id=guild_id,
        forum_channel_id=forum_channel_id
    )
    app.run()


if __name__ == "__main__":
    main()
