import os
import yaml
import sys
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))  # 日本時間 (UTC+9)

class PostedLinksManager:
    # ---------------------
    # コンストラクタ
    # ---------------------
    def __init__(self, posted_links_path):
        self.posted_links_path = posted_links_path

    # ---------------------
    # posted_links.yaml を読み込む
    # ---------------------
    def load(self):
        if os.path.exists(self.posted_links_path):
            with open(self.posted_links_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    # ---------------------
    # posted_links.yaml に書き込む
    # ---------------------
    def save(self, all_posted_links):
        with open(self.posted_links_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(all_posted_links, f, allow_unicode=True, default_flow_style=False)

    # ---------------------
    # 古い投稿リンクを削除する
    # ---------------------
    def clean_old_links(self, all_posted_links, expiration_days):
        now = datetime.now(JST)
        cutoff_time = now - timedelta(days=expiration_days)
        for genre, links in all_posted_links.items():
            all_posted_links[genre] = [
                link for link in links
                if datetime.strptime(link["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST) > cutoff_time
            ]
