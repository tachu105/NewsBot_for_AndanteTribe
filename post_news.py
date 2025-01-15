import feedparser
import requests
import os

# RSSフィードのURL
RSS_URL = "https://www.4gamer.net/rss/news_topics.xml"

# Discord Webhook URL（環境変数から取得）
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# RSSフィードをパース
feed = feedparser.parse(RSS_URL)
latest_news = feed.entries[:2]  # 最新2件を取得

# 空白にリンクを埋め込む形式でメッセージを作成
content = "**最新ニュース（4Gamer）**\n\n"
for item in latest_news:
    title = item.title
    link = item.link
    content += f"[ ]({link})\n"

# Discordに投稿
if DISCORD_WEBHOOK_URL:
    response = requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
    if response.status_code == 204:
        print("ニュースをDiscordに投稿しました。")
    else:
        print(f"投稿に失敗しました: {response.status_code}")
else:
    print("DISCORD_WEBHOOK_URLが設定されていません。")
