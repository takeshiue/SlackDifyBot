FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY . .

# ログディレクトリの作成
RUN mkdir -p /app/logs && chmod 755 /app/logs

# 実行時の環境変数設定
ENV PYTHONUNBUFFERED=1

# アプリケーションの実行
CMD ["python", "main.py"]