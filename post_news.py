import feedparser

# RSSフィードのURLを指定
rss_url = "https://example.com/rss"  # サンプルのRSSフィードURLに置き換えてください

# RSSフィードをパース
feed = feedparser.parse(rss_url)

# 結果を出力（埋め込みリンク形式）
for item in feed.entries:
    title = item.title
    link = item.link
    print(f"[{title}]({link})")
