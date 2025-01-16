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

        # カテゴリ -> (thread_id, thread_name) をキャッシュする辞書
        self.category_threads = {}

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
                print(f"[INFO] 既存スレッド発見: {t['name']} (ID: {t['id']}, アーカイブ: {t.get('archived', False)})")
                return (t["id"], t["name"], t.get("archived", False))
        print(f"[INFO] カテゴリ '{category_name}' の既存スレッドは見つかりません")
        return (None, None, None)

    # ---------------------
    # カテゴリに対応するスレッドを見つける or 作成
    # ---------------------
    def find_or_create_thread(self, category_name):
        thread_id, thread_name, is_archived = self.find_existing_thread(category_name)
        if thread_id:
            # もしアーカイブされていれば解除
            if is_archived:
                self.discord_service.unarchive_thread(thread_id)
            return thread_id, thread_name
        else:
            # 新規作成
            created_id = self.discord_service.create_thread(category_name, f"({category_name})に関するニュースをお届けします。")
            return created_id, category_name

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

        days_of_week = ["日", "月", "火", "水", "木", "金", "土"]

        # ジャンルごとに RSS → 投稿
        for genre, data in config["genres"].items():
            if genre not in all_posted_links:
                all_posted_links[genre] = []

            posted_links_set = {item["link"] for item in all_posted_links[genre]}
            rss_urls = data["rss_feeds"]

            # RSS エントリを取得
            all_entries = self.rss_service.fetch_rss_entries(rss_urls)
            # 未投稿のものだけに絞る
            new_entries = [e for e in all_entries if e["link"] not in posted_links_set]
            # リンクで重複を削除
            unique_entries = {entry["link"]: entry for entry in new_entries}.values()
            # 日付降順にソート & max_entries 件に絞る
            latest_entries = sorted(unique_entries, key=lambda x: x["published"], reverse=True)[:max_entries]

            # カテゴリ用のスレッドを取得
            if genre not in self.category_threads:
                thread_id, thread_name = self.find_or_create_thread(genre)
                self.category_threads[genre] = (thread_id, thread_name)
            else:
                thread_id, thread_name = self.category_threads[genre]

            # 投稿処理
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
                    content += f"[_]({entry['link']}) "
                    new_links.append({
                        "link": entry["link"],
                        "timestamp": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
                    })

                # メッセージ投稿
                success = self.discord_service.post_message(thread_id, content)
                if success:
                    # posted_links に追加
                    all_posted_links[genre].extend(new_links)
                    self.posted_links_manager.save(all_posted_links)
                else:
                    print(f"[ERROR] スレッド投稿に失敗: genre={genre}")
                    sys.exit(1)


# ---------------------
# スクリプトのエントリポイント
# ---------------------
def main():
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    guild_id = os.getenv("GUILD_ID")
    forum_channel_id = os.getenv("FORUM_CHANNEL_ID")

    base_dir = os.path.dirname(__file__)
    config_file_path = os.path.join(base_dir, '..', 'datas', 'config.yaml')
    posted_links_path = os.path.join(base_dir, '..', 'datas', 'posted_links.yaml')

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
