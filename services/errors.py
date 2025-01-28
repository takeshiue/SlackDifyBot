"""Custom error classes for the application"""

class DifyAPIError(Exception):
    """Base error class for Dify API related errors"""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class DifyTimeoutError(DifyAPIError):
    """Raised when Dify API request times out"""
    def __init__(self):
        super().__init__("応答がタイムアウトしました。しばらく待ってから再度お試しください。")

class DifyConnectionError(DifyAPIError):
    """Raised when connection to Dify API fails"""
    def __init__(self, original_error: Exception = None):
        super().__init__("APIサーバーとの接続に失敗しました。", original_error)

class DifyResponseError(DifyAPIError):
    """Raised when Dify API returns an unexpected response"""
    def __init__(self, response_data: dict = None):
        message = "予期しない応答形式を受信しました。"
        if response_data:
            message += f" 詳細: {response_data}"
        super().__init__(message)
