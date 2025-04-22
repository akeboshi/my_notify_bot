import requests
from bs4 import BeautifulSoup
import os
import sys
from datetime import datetime
import pytz # タイムゾーンの処理に必要

# --- 設定 ---
TARGET_URL = "https://kabutan.jp/stock/?code=2175" # 取得したい株価のURL
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL") # 環境変数からWebhook URLを取得
SLACK_BOT_NAME = "やる気スイッチ" # ここで名前を指定
SLACK_BOT_ICON = ":money_mouth_face:" # ここでアイコン絵文字を指定 (または SLACK_BOT_ICON_URL = "画像のURL")

# CSSセレクター
NAME_SELECTOR = "#stockinfo_i1 > div.si_i1_1 > h2"
CHANGE_SELECTOR = "#stockinfo_i1 > div.si_i1_2 > dl > dd:nth-child(2) > span"
PRICE_SELECTOR = "span.kabuka"
# --- 設定ここまで ---

def fetch_stock_info(url):
    """指定されたURLから株価情報を取得する"""
    try:
        response = requests.get(url, timeout=10) # 10秒でタイムアウト
        response.raise_for_status() # エラーがあれば例外を発生させる
        response.encoding = response.apparent_encoding # 文字コードを適切に設定
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}", file=sys.stderr)
        return None

def extract_data(soup, selector):
    """BeautifulSoupオブジェクトとCSSセレクターからテキストを抽出する"""
    element = soup.select_one(selector)
    if element:
        return element.get_text(strip=True)
    else:
        print(f"Error: Could not find element with selector '{selector}'", file=sys.stderr)
        return "取得失敗" # 要素が見つからない場合

def send_slack_notification(message):
    """Slackにメッセージを送信する (名前とアイコンを指定)"""
    if not SLACK_WEBHOOK_URL:
        print("Error: Slack Webhook URL is not set.", file=sys.stderr)
        return False

    payload = {
        "text": message,
        "username": SLACK_BOT_NAME,      # 投稿者名を設定
        "icon_emoji": SLACK_BOT_ICON,  # アイコン絵文字を設定 (どちらか一方)
        # "icon_url": "https://example.com/icon.png" # アイコンURLを設定 (どちらか一方、実際のURLに置き換えてください)
    }

    # icon_emoji を使いたい場合は、icon_urlの行をコメントアウトしてください
    # if SLACK_BOT_ICON and "icon_url" not in payload: # icon_url が指定されていない場合のみ icon_emoji を使う
    #     payload["icon_emoji"] = SLACK_BOT_ICON

    print(f"Sending payload: {payload}") # 送信するペイロード全体をログに出力

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        print("Successfully sent notification to Slack.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending notification to Slack: {e}", file=sys.stderr)
        if response is not None: # responseオブジェクトが存在すれば詳細を出力
            print(f"Response status code: {response.status_code}", file=sys.stderr)
            print(f"Response text: {response.text}", file=sys.stderr)
        return False

if __name__ == "__main__":
    print(f"Fetching stock info from {TARGET_URL}...")
    soup = fetch_stock_info(TARGET_URL)

    if soup:
        print("Extracting data...")
        stock_name = extract_data(soup, NAME_SELECTOR)
        stock_change = extract_data(soup, CHANGE_SELECTOR)
        stock_price = extract_data(soup, PRICE_SELECTOR)

        # 現在時刻（JST）を取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst).strftime('%Y-%m-%d %H:%M:%S JST')

        # Slackに送るメッセージを整形
        message = f"""
        現在時刻: {now_jst}
        銘柄名: {stock_name}
        株価: {stock_price}
        変化率: {stock_change}
        """
        print("Sending notification to Slack...")
        send_slack_notification(message)
    else:
        print("Failed to fetch stock information.", file=sys.stderr)
        sys.exit(1)
    print("Done.")
    # ここでスクリプトを終了
    sys.exit(0) 
