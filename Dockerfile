# ビルドステージ
FROM python:3.11-slim as builder

WORKDIR /app

# 必要なパッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 実行ステージ
FROM python:3.11-slim

WORKDIR /app

# 必要なパッケージのコピー
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/

# アプリケーションコードのコピー
COPY . .

# 実行時の環境変数設定
ENV PYTHONUNBUFFERED=1

# アプリケーションの実行
CMD ["python", "main.py"]
