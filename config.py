import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN") or "your-telegram-token-here"
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", 123456789))
DB_PATH = os.getenv("DB_PATH", "chat_settings.db")

BOT_USERNAME = os.getenv("BOT_USERNAME", "@YourBot")
MAX_HISTORY = 10
