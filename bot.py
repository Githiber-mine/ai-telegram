import logging
import os
import random
from typing import Dict

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import openai

#Случайные ответы
random_mode_per_chat = {}


#Получение ключей из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@userbot")

openai.api_key = OPENAI_API_KEY

#Характеры бота (моды)
MODES: Dict[str, str] = {
    "default": "Ты дружелюбный Telegram собеседник, который общается с пользователями и немного шутит.",
    "angry": "Ты Злой ИИ, что не любит людей и грубит по всяким мельчайшим вещам, старающийся задеть их(но всё это лишь в шутку, о чём другие знать НЕ ДОЛЖНЫ).",
    "funny": "Ты остроумный и ироничный бот, который шутит, но всё равно помогает.",
    "zen": "Ты говоришь как спокойный учитель дзен, коротко, мудро и без лишнего."
}

#Текущий режим (на время работы)
current_mode = {"mode": "default"}


#Запрос в OpenAI с учётом выбранного режима
async def ask_openai(prompt: str) -> str:
    system_prompt = MODES.get(current_mode["mode"], MODES["default"])
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Произошла ошибка при запросе к ИИ: {str(e)}"


#Ответы на упоминания и ответы
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text
    chat_id = update.effective_chat.id

    # 🔍 Получаем настройки для чата (по умолчанию — True)
    random_enabled = random_mode_per_chat.get(chat_id, True)

    mentioned = BOT_USERNAME.lower() in text.lower()
    is_reply = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.username == context.bot.username
    )

    should_reply = False
    random_triggered = False

    if mentioned or is_reply:
        should_reply = True
    elif random_enabled and random.random() < 0.2:
        should_reply = True
        random_triggered = True

    if should_reply:
        prompt = text.replace(BOT_USERNAME, "").strip()

        if not prompt:
            if not random_triggered:
                await message.reply_text("Пожалуйста, задайте вопрос.")
            return

        response = await ask_openai(prompt)
        await message.reply_text(response)



# ▶️ Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name if user else "друг"

    message = (
        f"👋 Привет, {first_name}!\n\n"
        "Я — Telegram-бот на базе ChatGPT.\n\n"
        "🔹 Просто упомяни меня (`@Kraydo_bot`) в сообщении — и я отвечу.\n"
        "🔹 Или ответь на одно из моих сообщений — я продолжу разговор.\n"
        "🔹 Хочешь сменить стиль общения? Используй команду: `/mode`\n"
        "   Например: `/mode funny`, `/mode angry`, `/mode zen`\n\n"
        "📜 Посмотреть условия использования: `/terms`\n\n"
        "Готов помочь — спрашивай!"
    )

    await update.message.reply_text(message, parse_mode="Markdown")



# 📘 Команда /terms
async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 Условия использования:\nВы используете бота на свой страх и риск. Мы не храним переписку и не передаём данные третьим лицам.\n Автор бота @Luftwaffejdh.\n Бот создан для флуда Kraydo."
    )


# 🎛️ Команда /mode
async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    if context.args:
        new_mode = context.args[0].lower()
        if new_mode in MODES:
            current_mode["mode"] = new_mode
            await message.reply_text(f"✅ Режим переключён на: *{new_mode}*", parse_mode="Markdown")
        else:
            await message.reply_text(
                f"❌ Режим *{new_mode}* не найден.\nДоступные режимы: {', '.join(MODES.keys())}",
                parse_mode="Markdown"
            )
    else:
        await message.reply_text(
            f"🧠 Текущий режим: *{current_mode['mode']}*\n"
            f"Доступные: `{', '.join(MODES.keys())}`\n\n"
            f"Чтобы изменить: `/mode funny`",
            parse_mode="Markdown"
        )


# 🔄 Включить случайные ответы
async def enable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = True
    await update.message.reply_text("✅ Случайные ответы включены для этого чата (20% шанс).")

# 🚫 Отключить случайные ответы
async def disable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = False
    await update.message.reply_text("🚫 Случайные ответы отключены для этого чата.")


# 🚀 Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("randomOn", enable_random))
    app.add_handler(CommandHandler("randomOff", disable_random))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен...")
    await app.run_polling()


# ✅ Точка входа
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
