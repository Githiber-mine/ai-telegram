import os

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Together API
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

# PostgreSQL / Railway Database
DATABASE_URL = os.getenv("DATABASE_URL")  # Пример: postgres://user:pass@host:port/dbname

# Имя бота (можно задать вручную или вытянуть через Telegram API)
BOT_USERNAME = os.getenv("BOT_USERNAME", "@your_bot_username")

BOT_USERNAME = os.getenv("BOT_USERNAME", "@YourBot")
MAX_HISTORY = 10
