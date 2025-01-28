import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logger():
    """Configure and return a logger instance"""
    logger = logging.getLogger('slack_bot')
    logger.setLevel(logging.DEBUG)  # より詳細なログを取得するためDEBUGレベルに設定

    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    # ファイルハンドラ（ローテーション付き）
    file_handler = RotatingFileHandler(
        'app.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)

    # 既存のハンドラをクリア
    logger.handlers.clear()

    # ハンドラを追加
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger