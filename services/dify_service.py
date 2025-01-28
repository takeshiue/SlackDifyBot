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
        self.base_url = 'https://dify.uematsu.cn/v1'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.timeout = 30  # タイムアウト時間（秒）

    def get_response(self, query: str, user: str, conversation_id: Optional[str] = None) -> str:
        """
        Get response from Dify API with enhanced error handling and monitoring

        Args:
            query (str): User's query text
            user (str): User identifier
            conversation_id (str, optional): ID for conversation tracking

        Returns:
            str: Response from Dify API

        Raises:
            DifyAPIError: Base class for all Dify related errors
            ValueError: If query is empty
        """
        if not query:
            logger.error("空のクエリを受信")
            raise ValueError("クエリが空です")

        data = {
            'query': query,
            'response_mode': 'blocking',
            'user': user,
            'conversation_id': conversation_id or '',
            'inputs': {}
        }

        start_time = datetime.now()
        try:
            logger.info(f"Dify APIリクエスト開始 - ユーザー: {user}")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()

            response_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Dify API応答時間: {response_time:.2f}秒")

            response_data = response.json()
            if 'answer' in response_data:
                return response_data['answer']
            else:
                logger.warning(f"予期しない応答形式: {response_data}")
                raise DifyResponseError(response_data)

        except requests.exceptions.Timeout:
            logger.error("Dify APIリクエストがタイムアウト")
            raise DifyTimeoutError()

        except requests.exceptions.RequestException as e:
            logger.error(f"Dify APIリクエストエラー: {str(e)}")
            raise DifyConnectionError(e)

        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise DifyAPIError(f"予期しないエラーが発生しました: {str(e)}", e)

        finally:
            response_time = (datetime.now() - start_time).total_seconds()
            if response_time > self.timeout * 0.8:  # タイムアウト閾値の80%を超えた場合
                logger.warning(f"応答時間が長い: {response_time:.2f}秒")