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
        self.base_url = os.environ.get('DIFY_API_URL', 'https://dify.uematsu.cn/v1')  # 環境変数から読み込み
        logger.info(f"Dify API URL: {self.base_url}")  # URLを確認するためのログを追加
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.timeout = 30  # タイムアウト時間を短縮

    def get_response(self, query: str, user: str, conversation_id: Optional[str] = None) -> str:
        """
        Get response from Dify API with enhanced error handling and monitoring
        """
        if not query:
            logger.error("空のクエリを受信")
            raise ValueError("クエリが空です")

        data = {
            'inputs': {},
            'query': query,
            'response_mode': 'blocking',
            'user': user
        }

        if conversation_id:
            data['conversation_id'] = conversation_id

        start_time = datetime.now()
        try:
            logger.info(f"Dify APIリクエスト開始 - ユーザー: {user}")
            logger.debug(f"リクエストURL: {self.base_url}")
            logger.debug(f"リクエストヘッダー: {self.headers}")
            logger.debug(f"リクエストデータ: {data}")

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=self.timeout
            )

            logger.debug(f"APIレスポンス状態コード: {response.status_code}")
            logger.debug(f"APIレスポンスヘッダー: {response.headers}")
            logger.debug(f"APIレスポンス本文: {response.text}")

            response.raise_for_status()
            response_data = response.json()

            response_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Dify API応答時間: {response_time:.2f}秒")

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
            logger.debug(f"詳細なエラー情報: {e.__class__.__name__}, {e.args}")
            raise DifyConnectionError(e)

        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            raise DifyAPIError(f"予期しないエラーが発生しました: {str(e)}", e)

        finally:
            response_time = (datetime.now() - start_time).total_seconds()
            if response_time > self.timeout * 0.8:
                logger.warning(f"応答時間が長い: {response_time:.2f}秒")