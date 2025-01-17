# NewsBot_by_GithubActions
## DiscordへのニュースRSS自動投稿Bot
GitHub ActionsとDiscord APIを利用して指定したRSSフィードの最新情報を取得し、それをDiscordのフォーラムスレッドに自動で投稿するためのツールです。時刻指定の定期実行と手動実行をサポートしています。

## 機能
### ・指定した複数のRSSフィードから最新記事を取得
  　Configで指定されたRSSフィードの情報を投稿日時でソートし、カテゴリ毎の最新記事を取得します。<br>
  　投稿毎の最大記事数はConfigから変更できます。
  
### ・Discordのフォーラムチャンネル内でカテゴリごとにスレッドに投稿
  　投稿毎にフォーラム内の既存スレッド（アクティブ,公開アーカイブ）を解析し、カテゴリ名と同名のスレッドに記事を投稿します。<br>
  　既存スレッドが発見されなかった場合は、新規スレッドを立ち上げます。
  
### ・スケジュール実行（毎日指定した時刻）と手動実行をサポート
  　workflowで指定された時刻に、actionを自動実行して記事を投稿します。<br>
  　またActionsタブからの手動実行もサポートしています。
  
### ・投稿済みリンクを管理し、重複投稿を防止
  　履歴に記録されている記事は除外して情報を取得しています。<br>
  　履歴の保持期間はConfigから変更できます。
  
### ・エラー発生時にはDiscordに通知
  　Actionの実行エラー発生時に、指定のWebHookに通知します。
  
## 必要要件
- Python 3.9 以上
- GitHub Actions
- Discord Bot API（適切な権限が設定されたトークンが必要）
- RSSフィードのURL
- 環境変数
以下の環境変数をGitHub Secretsに設定してください：

| 環境変数名 |	説明 |
| --- | --- |
| DISCORD_BOT_TOKEN |	Discord Botのトークン|
| GUILD_ID | DiscordサーバーのID |
| FORUM_CHANNEL_ID | DiscordフォーラムチャンネルのID |
| POST_ERROR_NOTIFICATION | エラー発生時に通知を送るDiscord WebhookのURL |

<br><br><br>
# 設定変更方法
## ニュースのカテゴリ、RSSフィードを変更する
 `datas/config.yaml` 内のジャンル設定項目を書き換える
 
 ```yaml
genres:
  [カテゴリ名]:
    rss_feeds:
      # コメントでフィードの名前を記載してください
      - "[RSSフィードのリンク]"
 ```

※ カテゴリ名が投稿されるスレッド名となります。<br>
※ フィードの認識には `feedparser` を使用しています。

## 投稿記事数と履歴保持期間を設定する
  `datas/config.yaml` 内のグローバル設定項目の各変数値を変更する

  ```yaml
  # グローバル設定
  expiration_days: 3  # 投稿履歴の保持期間（日）
  max_entries: 10  # 一投稿あたりの最大記事数
  ```

## 自動投稿時間を変更する
  `.github/worlflow/news_to_discord.yml` の `cron` データを書き換える
  
  ```yaml
  on:
    schedule:
      - cron: "0 22 * * *"  # 投稿時間1
      - cron: "0 4 * * *"   # 投稿時間2
      - cron: "0 10 * * *"  # 投稿時間3
  ```

  ※ フォーマット：`"分 時 日 月 曜日"`<br>
  ※ UTC時間に変換して記載してください。（UTC = JTC - 9時間）

## 投稿するチャンネルを変える
1. Discordの `ユーザー設定/詳細設定/開発者モード` を有効にする
2. 該当のフォーラムを右クリックし、チャンネルIDを取得する
3. `Github/Setting/Secrets and variables/Actions/Repository secrests/FORUM_CHANNNEL_ID` にチャンネルIDを設定する

## 投稿するサーバーを変更する
1. 下記のリンクからBotを招待する
   ```
   https://discord.com/oauth2/authorize?client_id=1329355732537184256&permissions=326417590272&integration_type=0&scope=bot
   ```
3. Discordの `ユーザー設定/詳細設定/開発者モード` を有効にする
4. サーバー名を右クリックし、サーバーIDを取得する
5. `Github/Setting/Secrets and variables/Actions/Repository secrests/GUILD_ID` にサーバーIDを設定する

## エラー発生時の通知先を変更する
1. 通知するサーバーの `サーバー設定/アプリ/連携サービス/ウェブフック` からウェブフックを作成し、ウェブフックURLをコピーする
2. `Github/Setting/Secrets and variables/Actions/Repository secrests/POST_ERROR_NOTIFICATION` にウェブフックURLを設定する

## BotAPIの詳細を設定する
[BotAPI設定ページ](https://discord.com/developers/applications/1329355732537184256/information)
　※やげっちのゲーム用アカウントでログインする
- **トークンの発行**
  1. `Bot/TOKEN` からResetTokenで新規トークンを発行
  2. `Github/Setting/Secrets and variables/Actions/Repository secrests/DISCORD_BOT_TOKEN` にトークンを設定する
- **新規招待リンクを発行**
  1. `OAuth2/OAuth2 URL Generator` でBotにチェック
  2. BotPermissionsは「SendMessages、CreatePublicThreads、SendMessagesinThreads、ManageMessages、ManageThreads、ReadMessageHistory」にチェックを入れた状態で動作確認済

<br><br><br>
# 注意
- `requirements.txt` には使用するライブラリを記載しています。このデータが変更されるとキャッシュの再構成により初回実行時間が長くなるため、不用意な変更は行わないようにしてください。
- このレポジトリはGithub Actionの無料枠を使用するためにpublic設定となっています。
- 投稿履歴は `posted_links.yaml` で管理されています。実行時にファイルが見つからない場合は自動で再生成されますが、内部形状が崩れるとエラーとなる可能性があります。
  
