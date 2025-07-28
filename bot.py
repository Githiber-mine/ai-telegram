import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_TOKEN
from utils.logger import logger
from core.handlers import (
    start_command,
    terms_command,
    mode_command,
    enable_random,
    disable_random,
    secret_command,
    handle_message,
)

async def main():
    logger.info("🚀 Запуск Telegram-бота...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # ✅ Регистрируем команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("randomon", enable_random))
    app.add_handler(CommandHandler("randomoff", disable_random))
    app.add_handler(CommandHandler("secret", secret_command))

    # 📨 Обработка всех остальных текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен.")
