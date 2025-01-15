import re
import feedparser
import requests
from bs4 import BeautifulSoup
import os

# GoogleニュースRSSフィードURL（日本語）
RSS_URL = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def clean_html(raw_html):
    """HTMLタグを除去する関数"""
    cleanr = re.compile('<.*?>')
    clean_text = re.sub(cleanr, '', raw_html)
    return clean_text

def get_image_url(entry):
    """RSSエントリから画像URLを取得する"""
    # media:content タグをチェック
    if 'media_content' in entry:
        return entry.media_content[0]['url']
    
    # enclosure タグをチェック（画像が含まれることがある）
    for link in entry.links:
        if link['type'].startswith('image'):
            return link['href']
    
    # 代替画像を返す
    return "https://www.google.com/s2/favicons?sz=128&domain=news.google.com"

def post_to_discord(entry):
    """Discordに記事を投稿する"""
    title = entry.title
    link = entry.link
    description = clean_html(entry.summary) if hasattr(entry, 'summary') else "詳しくはリンク先をご覧ください。"
    image_url = get_image_url(entry)
    
    payload = {
        "embeds": [
            {
                "title": title,
                "url": link,
                "description": description,
                "thumbnail": {
                    "url": image_url
                }
            }
        ]
    }
    
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print("Posted to Discord successfully.")
    else:
        print(f"Failed to post: {response.status_code}, {response.text}")

def get_latest_news():
    """RSSフィードから最新の記事を取得"""
    feed = feedparser.parse(RSS_URL)
    latest_entries = feed.entries[:5]  # 最新5件を取得
    return latest_entries

def main():
    """メイン処理"""
    latest_news = get_latest_news()
    for entry in latest_news:
        post_to_discord(entry)
        print(entry)

if __name__ == "__main__":
    main()
