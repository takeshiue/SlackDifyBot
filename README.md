# Slackdifybot

A Slack bot that integrates with Dify API to provide automated responses to mentions.

## Features
- Responds to mentions in Slack channels
- Integrates with Dify API for intelligent responses
- Handles conversation history
- Provides usage statistics

## Setup

1. Clone this repository
2. Copy `.env.example` to `.env` and configure the following environment variables:

   ```bash
   # Slack Configuration
   SLACK_BOT_TOKEN=      # Bot User OAuth Token from Slack
   SLACK_APP_TOKEN=      # App-Level Token from Slack

   # Dify API Configuration
   DIFY_API_KEY=        # Your Dify API Key
   DIFY_API_URL=        # Your Dify API URL (e.g., https://api.dify.ai/v1)

   # Database Configuration
   DATABASE_URL=        # PostgreSQL connection URL
   ```

3. Run the bot using the Run button in Replit

## Environment Variables

- `SLACK_BOT_TOKEN`: Botユーザーのトークン（xoxb-で始まる）
- `SLACK_APP_TOKEN`: アプリレベルトークン（xapp-で始まる）
- `DIFY_API_KEY`: Dify APIのアクセスキー
- `DIFY_API_URL`: Dify APIのエンドポイントURL
- `DATABASE_URL`: PostgreSQLデータベースの接続URL