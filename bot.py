import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from utils.logger import logger
from core.handler import handle_message, mode_command
from core.database import init_db
from utils.auth import load_admins

# ✅ Загрузка админов
ADMINS = load_admins()

# ✅ Главная функция запуска
async def main():
    # Инициализация базы данных
    await init_db()

    # Создание приложения Telegram
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    # Обработчики команд и сообщений
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logger.info("🤖 Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
