import re
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, parse_qs
from time import sleep

# GoogleアラートRSSフィードURL
RSS_URL = "https://www.google.co.jp/alerts/feeds/11500782125501094599/1622788681073332472"

# Discord Webhook URL (環境変数から取得することを推奨)
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

def is_scraping_allowed(site_url, path="/"):
    """指定サイトの特定パスがスクレイピング可能かを判別"""
    parsed_url = urlparse(site_url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"

    rp = RobotFileParser()
    rp.set_url(robots_url)
    for _ in range(3):  # 3回リトライ
        try:
            rp.read()
            return rp.can_fetch("*", f"{parsed_url.scheme}://{parsed_url.netloc}{path}")
        except:
            print(f"Retrying to read robots.txt from {robots_url}")
            sleep(1)  # 1秒待機してリトライ
    print(f"Failed to read robots.txt from {robots_url} after retries")
    return False

def fetch_og_image(url):
    """元記事のURLからOGP画像のURLを取得"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image['content']
    return None

def post_to_discord(title, link, image_url):
    """Discordに記事を投稿する"""
    payload = {
        "embeds": [
            {
                "title": title,
                "url": link,
                "thumbnail": {"url": image_url} if image_url else None
            }
        ]
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 204:
        print(f"Posted to Discord successfully: {title}")
    else:
        print(f"Failed to post: {response.status_code}, {response.text}")

def extract_original_url(google_url):
    """GoogleリダイレクトURLから元記事のURLを抽出"""
    parsed_url = urlparse(google_url)
    query_params = parse_qs(parsed_url.query)
    if "url" in query_params:
        return query_params["url"][0]  # 元記事のURLを返す
    return google_url  # 抽出できなければ元のURLを返す

def process_feed():
    """RSSフィードを処理してスクレイピング許可を確認し、Discordに投稿"""
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries[:5]:  # 最新5件を取得
        title = entry.title
        link = extract_original_url(entry.link)  # 元記事のURLを抽出
        parsed_link = urlparse(link)
        site_url = f"{parsed_link.scheme}://{parsed_link.netloc}"

        if is_scraping_allowed(site_url, parsed_link.path):
            print(f"Scraping allowed for {link}")
            image_url = fetch_og_image(link)
            post_to_discord(title, link, image_url)
        else:
            print(f"Scraping not allowed for {link}")

# メイン処理の実行
if __name__ == "__main__":
    process_feed()
