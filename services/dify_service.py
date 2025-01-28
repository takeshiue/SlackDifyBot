import os
import requests
from typing import Optional
from datetime import datetime
from utils.logger import setup_logger
from .errors import DifyAPIError, DifyTimeoutError, DifyConnectionError, DifyResponseError

logger = setup_logger()

class DifyService:
    """Service class for interacting with Dify API"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Dify API keyが必要です")
        self.api_key = api_key
        self.base_url = os.environ.get('DIFY_API_URL', 'http://dify.uematsu.cn/v1')
        logger.info(f"Dify API URL: {self.base_url}")
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.timeout = 30

    def get_response(self, query: str, user: str, conversation_id: Optional[str] = None) -> str:
        """
        Get response from Dify API with enhanced error handling and monitoring
        """
        if not query:
            logger.error("空のクエリを受信")
            raise ValueError("クエリが空です")

        # APIリクエストデータの構築
        data = {
            'inputs': {},
            'query': query,
            'user': user,
            'response_mode': 'blocking',
        }

        if conversation_id:
            data['conversation_id'] = conversation_id

        start_time = datetime.now()
        try:
            logger.info(f"Dify APIリクエスト開始 - ユーザー: {user}")
            logger.debug(f"リクエストURL: {self.base_url}/chat-messages")
            logger.debug(f"リクエストデータ: {data}")

            # Chat Message APIエンドポイントにリクエスト
            response = requests.post(
                f"{self.base_url}/chat-messages",
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )

            logger.debug(f"APIレスポンス状態コード: {response.status_code}")
            response.raise_for_status()
            response_data = response.json()
            logger.debug(f"APIレスポンス: {response_data}")

            if 'answer' in response_data:
                return response_data['answer']
            elif 'message' in response_data:
                return response_data['message']
            else:
                logger.warning(f"予期しない応答形式: {response_data}")
                raise DifyResponseError(response_data)

        except requests.exceptions.Timeout:
            logger.error("Dify APIリクエストがタイムアウト")
            raise DifyTimeoutError()

        except requests.exceptions.RequestException as e:
            logger.error(f"Dify APIリクエストエラー: {str(e)}")
            logger.debug(f"詳細なエラー情報: {e.__class__.__name__}, {e.args}")
            raise DifyConnectionError(e)

        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise DifyAPIError(f"予期しないエラーが発生しました: {str(e)}", e)

        finally:
            response_time = (datetime.now() - start_time).total_seconds()
            if response_time > self.timeout * 0.8:
                logger.warning(f"応答時間が長い: {response_time:.2f}秒")

    def get_conversation_history(self, user: str, conversation_id: str) -> list:
        """会話履歴を取得"""
        try:
            response = requests.get(
                f"{self.base_url}/messages",
                params={'conversation_id': conversation_id},
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json().get('data', [])
        except Exception as e:
            logger.error(f"会話履歴の取得に失敗: {str(e)}")
            raise DifyAPIError("会話履歴の取得に失敗しました", e)