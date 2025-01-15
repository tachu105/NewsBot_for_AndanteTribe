import feedparser
import requests
import os

# GoogleニュースRSSフィードURL（日本語）
RSS_URL = "https://www.google.co.jp/alerts/feeds/11500782125501094599/1622788681073332472"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    latest_entries = feed.entries[:5]  # 最新5件を取得
    return latest_entries

def post_to_discord(entry):
    title = entry.title
    link = entry.link
    message = f"**{title}**\n{link}"
    
    payload = {
        "content": message
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Posted to Discord successfully.")
    else:
        print(f"Failed to post: {response.status_code}, {response.text}")

def main():
    latest_news = get_latest_news()
    for entry in latest_news:
        post_to_discord(entry)

if __name__ == "__main__":
    main()
