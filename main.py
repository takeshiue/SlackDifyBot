import os
import time
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from services.dify_service import DifyService
from services.conversation_service import ConversationService
from utils.logger import setup_logger
from services.errors import DifyAPIError, DifyTimeoutError, DifyConnectionError, DifyResponseError

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

# Initialize services
try:
    app = App(token=SLACK_BOT_TOKEN)
    dify_service = DifyService(api_key=DIFY_API_KEY)
    conversation_service = ConversationService()
    logger.info("Slackアプリの初期化が完了しました")
except Exception as e:
    logger.error(f"Slackアプリの初期化エラー: {str(e)}")
    raise

def format_stats_message(stats: dict) -> str:
    """統計情報をSlackメッセージ形式に整形"""
    message = []
    message.append("*使用統計情報*\n")
    message.append(f"• 総会話数: {stats['total_conversations']}")
    message.append(f"• 平均応答時間: {stats['avg_response_time']:.2f}秒")
    message.append(f"• エラー率: {stats['error_rate']:.1f}%")

    if 'recent_conversations' in stats:
        message.append("\n*最近の会話*")
        for conv in stats['recent_conversations'][:3]:  # 最新3件のみ表示
            message.append(f"• {conv['created_at'].strftime('%Y-%m-%d %H:%M')} - {conv['message'][:50]}...")

    if 'total_users' in stats:
        message.append(f"\n• 総ユーザー数: {stats['total_users']}")

    return "\n".join(message)

@app.command("/stats")
def handle_stats_command(ack, command, say):
    """統計情報表示コマンドの処理"""
    ack()
    logger.info(f"統計情報コマンド実行 - ユーザー: {command['user_id']}")

    try:
        if command.get('text') == 'all':
            # 全体の統計情報を取得（管理者用）
            stats = conversation_service.get_total_stats()
            say(format_stats_message(stats))
        else:
            # ユーザー個別の統計情報を取得
            stats = conversation_service.get_user_stats(command['user_id'])
            say(format_stats_message(stats))

    except Exception as e:
        error_message = "統計情報の取得中にエラーが発生しました。"
        logger.error(f"統計情報取得エラー: {str(e)}")
        say(error_message)

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

        # 応答時間の計測開始
        start_time = time.time()

        try:
            # Dify APIからの応答を取得
            response = dify_service.get_response(query, user)

            # 応答時間の計算（秒単位）
            response_time = time.time() - start_time

            # 会話を保存
            conversation_service.save_conversation(user, query, response, response_time)

            say(response)

        except DifyTimeoutError:
            error_message = "申し訳ありません。応答がタイムアウトしました。しばらく待ってから再度お試しください。"
            logger.error("Dify APIタイムアウト")
            say(error_message)
            conversation_service.save_conversation(user, query, error_message, time.time() - start_time, error_occurred=True)

        except DifyConnectionError as e:
            error_message = "申し訳ありません。APIサーバーとの接続に問題が発生しました。"
            logger.error(f"Dify API接続エラー: {str(e.original_error)}")
            say(error_message)
            conversation_service.save_conversation(user, query, error_message, time.time() - start_time, error_occurred=True)

        except DifyResponseError as e:
            error_message = "申し訳ありません。応答の処理中にエラーが発生しました。"
            logger.error(f"Dify API応答エラー: {str(e)}")
            say(error_message)
            conversation_service.save_conversation(user, query, error_message, time.time() - start_time, error_occurred=True)

        except DifyAPIError as e:
            error_message = "申し訳ありません。予期しないエラーが発生しました。"
            logger.error(f"Dify APIエラー: {str(e)}")
            say(error_message)
            conversation_service.save_conversation(user, query, error_message, time.time() - start_time, error_occurred=True)

    except Exception as e:
        error_message = "申し訳ありません。システムエラーが発生しました。"
        logger.error(f"システムエラー: {str(e)}")
        say(error_message)

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
        logger.error("必要な権限: app_mentions:read, chat:write, commands")
        raise

def main():
    """Main application entry point"""
    logger.info("Slackボットアプリケーションを起動します")
    try:
        # トークンのフォーマット検証を実行
        logger.info("トークンのフォーマットを検証中...")

        # SLACK_APP_TOKENの検証
        if not SLACK_APP_TOKEN.startswith("xapp-"):
            logger.error("SLACK_APP_TOKENの形式が正しくありません")
            raise ValueError("SLACK_APP_TOKENは'xapp-'で始まる必要があります")
        logger.info("SLACK_APP_TOKENのフォーマットは正常です")

        # SLACK_BOT_TOKENの検証
        if not SLACK_BOT_TOKEN.startswith("xoxb-"):
            logger.error("SLACK_BOT_TOKENの形式が正しくありません")
            raise ValueError("SLACK_BOT_TOKENは'xoxb-'で始まる必要があります")
        logger.info("SLACK_BOT_TOKENのフォーマットは正常です")

        # Initialize and verify Slack connection
        bot_user_id = initialize_slack()
        logger.info("Slack接続の初期化が完了しました")

        # Start Socket Mode handler
        logger.info("Socket Modeハンドラを開始します...")
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
        logger.info("Socket Modeハンドラが正常に開始されました")

    except Exception as e:
        logger.error("Slackアプリの起動に失敗しました: %s", str(e))
        logger.error("SLACK_APP_TOKENとSLACK_BOT_TOKENの設定を確認してください")
        raise

if __name__ == "__main__":
    main()