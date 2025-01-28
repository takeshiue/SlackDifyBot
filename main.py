import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from services.dify_service import DifyService
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()

def get_required_env_var(var_name: str) -> str:
    """Get required environment variable or exit with error"""
    value = os.environ.get(var_name)
    if not value:
        logger.error(f"環境変数 {var_name} が設定されていません")
        raise ValueError(f"環境変数 {var_name} が設定されていません")
    return value

# Initialize required environment variables
try:
    SLACK_BOT_TOKEN = get_required_env_var("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = get_required_env_var("SLACK_APP_TOKEN")
    DIFY_API_KEY = get_required_env_var("DIFY_API_KEY")
except ValueError as e:
    logger.error(f"環境変数エラー: {str(e)}")
    raise

# Initialize Slack app and Dify service
try:
    app = App(token=SLACK_BOT_TOKEN)
    dify_service = DifyService(api_key=DIFY_API_KEY)
    logger.info("Slackアプリの初期化が完了しました")
except Exception as e:
    logger.error(f"Slackアプリの初期化エラー: {str(e)}")
    raise

def initialize_slack():
    """Initialize Slack connection and verify bot credentials"""
    try:
        auth_test = app.client.auth_test()
        bot_user_id = auth_test["user_id"]
        logger.info("Slack接続成功: Bot User ID = %s", bot_user_id)
        logger.info("Bot名: %s, チーム: %s", auth_test.get("user"), auth_test.get("team"))
        logger.info("認証スコープ: %s", auth_test.get("scope", "不明"))
        return bot_user_id
    except Exception as e:
        logger.error("Slack接続エラー: %s", str(e))
        logger.error("トークンと権限の設定を確認してください")
        logger.error("必要な権限: app_mentions:read, chat:write")
        raise

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle mentions to the bot and respond with Dify API responses"""
    logger.info("メンションイベント受信: %s", event)

    if not event or 'text' not in event:
        logger.warning("メッセージの内容を取得できませんでした: %s", event)
        say("申し訳ありません。メッセージを処理できませんでした。")
        return

    try:
        bot_user_id = app.client.auth_test()["user_id"]
        query = event['text'].replace(f"<@{bot_user_id}>", "").strip()
        user = event['user']

        response = dify_service.get_response(query, user)
        say(response)
    except Exception as e:
        error_message = "申し訳ありません。リクエストの処理中にエラーが発生しました。"
        logger.error("リクエスト処理エラー: %s", str(e))
        say(error_message)

def main():
    """Main application entry point"""
    logger.info("Slackボットアプリケーションを起動します")
    try:
        if not SLACK_APP_TOKEN.startswith("xapp-"):
            logger.error("SLACK_APP_TOKENの形式が正しくありません")
            raise ValueError("SLACK_APP_TOKENは'xapp-'で始まる必要があります")

        if not SLACK_BOT_TOKEN.startswith("xoxb-"):
            logger.error("SLACK_BOT_TOKENの形式が正しくありません")
            raise ValueError("SLACK_BOT_TOKENは'xoxb-'で始まる必要があります")

        # Initialize and verify Slack connection
        bot_user_id = initialize_slack()

        # Start Socket Mode handler
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    except Exception as e:
        logger.error("Slackアプリの起動に失敗しました: %s", str(e))
        logger.error("SLACK_APP_TOKENとSLACK_BOT_TOKENの設定を確認してください")
        raise

if __name__ == "__main__":
    main()