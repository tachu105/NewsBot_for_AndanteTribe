import re
import feedparser
import requests
from bs4 import BeautifulSoup
import os

RSS_URL = "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    clean_text = re.sub(cleanr, '', raw_html)
    return clean_text

def get_image_from_article(url):
    """リンク先の記事から画像を取得する"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        # 最初に見つかった <img> タグの src を取得
        image = soup.find("img")
        if image and "src" in image.attrs:
            return image["src"]
    except Exception as e:
        print(f"Error fetching image: {e}")
    return "https://www.google.com/s2/favicons?sz=128&domain=news.google.com"  # 代替画像

def get_latest_news():
    feed = feedparser.parse(RSS_URL)
    latest_entries = feed.entries[:5]  # 最新5件を取得
    return latest_entries

def post_to_discord(entry):
    title = entry.title
    link = entry.link
    description = clean_html(entry.summary) if hasattr(entry, 'summary') else "詳しくはリンク先をご覧ください。"
    image_url = get_image_from_article(link)
    
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

def main():
    latest_news = get_latest_news()
    for entry in latest_news:
        post_to_discord(entry)

if __name__ == "__main__":
    main()
