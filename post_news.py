# ヘッダーを付けるかどうかを制御するフラグ
header_added = False

# 日本語の曜日リスト
days_of_week = ["日", "月", "火", "水", "木", "金", "土"]

# 5件ずつに分割して投稿
for i in range(0, len(latest_entries), CHUNK_SIZE):
    chunk = latest_entries[i:i + CHUNK_SIZE]
    
    # ヘッダーは最初の投稿にのみ付ける
    content = ""
    if not header_added:
        # 日本時間の現在時刻を取得してフォーマット
        now = datetime.now(JST)
        current_time = now.strftime("%m月%d日（")
        current_time += days_of_week[now.weekday()]  # 曜日を追加
        current_time += now.strftime("）%H時")
        content += f"**{current_time} 最新ニュース（{genre.capitalize()}）**\n\n"
        header_added = True

    new_links = []  # 新しく投稿したリンクを保持
    for entry in chunk:
        content += f"<{entry['link']}>\n"
        new_links.append({
            "link": entry["link"],
            "timestamp": datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S")
        })  # 新しいリンクとタイムスタンプを追加

    if webhook_url and new_links:
        response = requests.post(webhook_url, json={"content": content})
        if response.status_code == 204:
            print(f"ニュースをDiscordに投稿しました: {genre}（{i + 1}件目以降）")
            # 投稿が成功した場合のみ、投稿済みリンクを保存
            all_posted_links[genre].extend(new_links)  # 辞書に更新内容を反映
            save_posted_links(all_posted_links)
        else:
            print(f"投稿に失敗しました: {response.status_code}")
            # 最初の投稿が失敗した場合はヘッダーを次に付ける
            if i == 0:
                header_added = False
