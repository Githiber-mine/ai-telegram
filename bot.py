import asyncio
import nest_asyncio  # добавляем это
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)
from config import TELEGRAM_TOKEN
from utils.logger import logger
from utils.notify_admin import notify_admin
from db.database import init_db, load_chat_settings
from core.handlers import (
    start_command,
    terms_command,
    mode_command,
    enable_random,
    disable_random,
    secret_command,
    handle_message,
    say_command,
)

async def main():
    logger.info("🚀 Запуск Telegram-бота...")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    await app.bot.delete_webhook(drop_pending_updates=True)

    # ✅ Регистрируем команды
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("randomon", enable_random))
    app.add_handler(CommandHandler("randomoff", disable_random))
    app.add_handler(CommandHandler("secret", secret_command))
    app.add_handler(CommandHandler("say", say_command))

    # 📨 Обработка всех остальных текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await init_db()
    await load_chat_settings()

    await notify_admin(app.bot, "🤖 Бот запущен и готов к работе!")

    await app.run_polling()

if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()  # <--- нужно для Railway и других async-сред
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("🛑 Бот остановлен.")
