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
        logger.error(f"Required environment variable {var_name} is not set")
        raise ValueError(f"Required environment variable {var_name} is not set")
    return value

# Initialize required environment variables
try:
    SLACK_BOT_TOKEN = get_required_env_var("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = get_required_env_var("SLACK_APP_TOKEN")
    DIFY_API_KEY = get_required_env_var("DIFY_API_KEY")
except ValueError as e:
    logger.error(f"Environment variable error: {str(e)}")
    raise

# Initialize Slack app and Dify service
app = App(token=SLACK_BOT_TOKEN)
dify_service = DifyService(api_key=DIFY_API_KEY)

def initialize_slack():
    """Initialize Slack connection and verify bot credentials"""
    try:
        bot_user_id = app.client.auth_test()["user_id"]
        logger.info("Slack connection successful: Bot User ID = %s", bot_user_id)
        return bot_user_id
    except Exception as e:
        logger.error("Slack connection error: %s", str(e))
        raise

# Initialize bot user ID
bot_user_id = initialize_slack()

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle mentions to the bot and respond with Dify API responses"""
    logger.info("Mention event received: %s", event)

    if not event or 'text' not in event:
        logger.warning("Could not get message content: %s", event)
        say("申し訳ありません。メッセージを処理できませんでした。")
        return

    # Extract query by removing the mention
    query = event['text'].replace(f"<@{bot_user_id}>", "").strip()
    user = event['user']

    try:
        response = dify_service.get_response(query, user)
        say(response)
    except Exception as e:
        error_message = "申し訳ありません。リクエストの処理中にエラーが発生しました。"
        logger.error("Error processing request: %s", str(e))
        say(error_message)

def main():
    """Main application entry point"""
    logger.info("Starting Slack bot application")
    try:
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        handler.start()
    except Exception as e:
        logger.error("Failed to start Slack app: %s", str(e))
        raise

if __name__ == "__main__":
    main()