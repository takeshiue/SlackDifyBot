import os
from datetime import datetime
import psycopg2
from psycopg2.extras import DictCursor
from utils.logger import setup_logger

logger = setup_logger()

class ConversationService:
    def __init__(self):
        self.db_url = os.environ["DATABASE_URL"]
        self._init_database()

    def _init_database(self):
        """Initialize database tables if they don't exist"""
        with psycopg2.connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        response_time FLOAT,
                        error_occurred BOOLEAN DEFAULT FALSE
                    )
                """)
                conn.commit()
                logger.info("データベーステーブルの初期化が完了しました")

    def save_conversation(self, user_id: str, message: str, response: str, response_time: float, error_occurred: bool = False):
        """Save a conversation to the database"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO conversations 
                        (user_id, message, response, response_time, error_occurred)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (user_id, message, response, response_time, error_occurred))
                    conn.commit()
                    logger.info(f"会話履歴を保存しました - ユーザー: {user_id}")
        except Exception as e:
            logger.error(f"会話履歴の保存に失敗しました: {str(e)}")
            raise

    def get_user_history(self, user_id: str, limit: int = 10) -> list:
        """Get conversation history for a specific user"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM conversations
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"会話履歴の取得に失敗しました: {str(e)}")
            raise

    def get_user_stats(self, user_id: str) -> dict:
        """Get usage statistics for a specific user"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    # 総会話数
                    cur.execute("""
                        SELECT COUNT(*) as total_conversations,
                               COUNT(*) FILTER (WHERE error_occurred = true) as error_count,
                               AVG(response_time) as avg_response_time
                        FROM conversations
                        WHERE user_id = %s
                    """, (user_id,))
                    stats = dict(cur.fetchone())

                    # エラー率の計算
                    total = stats['total_conversations']
                    stats['error_rate'] = (stats['error_count'] / total * 100) if total > 0 else 0

                    # 最近の会話
                    cur.execute("""
                        SELECT created_at, message, response, response_time
                        FROM conversations
                        WHERE user_id = %s
                        ORDER BY created_at DESC
                        LIMIT 5
                    """, (user_id,))
                    stats['recent_conversations'] = [dict(row) for row in cur.fetchall()]

                    return stats
        except Exception as e:
            logger.error(f"統計情報の取得に失敗しました: {str(e)}")
            raise

    def get_total_stats(self) -> dict:
        """Get overall usage statistics"""
        try:
            with psycopg2.connect(self.db_url) as conn:
                with conn.cursor(cursor_factory=DictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            COUNT(DISTINCT user_id) as total_users,
                            COUNT(*) as total_conversations,
                            AVG(response_time) as avg_response_time,
                            COUNT(*) FILTER (WHERE error_occurred = true) as total_errors
                        FROM conversations
                    """)
                    stats = dict(cur.fetchone())

                    # エラー率の計算
                    total = stats['total_conversations']
                    stats['error_rate'] = (stats['total_errors'] / total * 100) if total > 0 else 0

                    return stats
        except Exception as e:
            logger.error(f"全体統計情報の取得に失敗しました: {str(e)}")
            raise