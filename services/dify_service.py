import requests
from typing import Optional
from utils.logger import setup_logger

logger = setup_logger()

class DifyService:
    """Service class for interacting with Dify API"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Dify API key is required")
        self.api_key = api_key
        self.base_url = 'https://dify.uematsu.cn/V1'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def get_response(self, query: str, user: str, conversation_id: Optional[str] = None) -> str:
        """
        Get response from Dify API

        Args:
            query (str): User's query text
            user (str): User identifier
            conversation_id (str, optional): ID for conversation tracking

        Returns:
            str: Response from Dify API

        Raises:
            ValueError: If query is empty
            Exception: If API request fails
        """
        if not query:
            logger.error("Empty query received")
            raise ValueError("クエリが空です")

        data = {
            'query': query,
            'response_mode': 'blocking',
            'user': user,
            'conversation_id': conversation_id or '',
            'inputs': {}
        }

        try:
            logger.info(f"Sending request to Dify API for user {user}")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            response_data = response.json()
            logger.info("Successfully received Dify API response")

            if 'answer' in response_data:
                return response_data['answer']
            else:
                logger.warning("Unexpected response format from Dify API: %s", response_data)
                return "申し訳ありません。予期しない応答形式を受信しました。"

        except requests.exceptions.Timeout:
            logger.error("Dify API request timed out")
            raise Exception("Dify APIがタイムアウトしました")
        except requests.exceptions.RequestException as e:
            logger.error("Dify API request failed: %s", str(e))
            raise Exception(f"Dify APIとの通信に失敗しました: {str(e)}")