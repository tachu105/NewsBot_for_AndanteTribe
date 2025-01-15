import re
import feedparser
import requests
import os

# GoogleニュースRSSフィードURL（日本語）
RSS_URL = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def clean_html(raw_html):
    """HTMLタグを除去する関数"""
    cleanr = re.compile('<.*?>')
    clean_text = re.sub(cleanr, '', raw_html)
    return clean_text

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    latest_entries = feed.entries[:5]  # 最新5件を取得
    return latest_entries

def post_to_discord(entry):
    title = entry.title
    link = entry.link
    description = clean_html(entry.summary) if hasattr(entry, 'summary') else "詳しくはリンク先をご覧ください。"
    
    payload = {
        "embeds": [
            {
                "title": title,
                "url": link,
                "description": description,
                "thumbnail": {
                    "url": "https://www.google.com/s2/favicons?sz=64&domain=news.google.com"
                }
            }
        ]
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
