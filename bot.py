from logger import logger
import os
from typing import Dict

import json

#загрузка настроек из json
SETTINGS_FILE = "chat_settings.json"

def load_chat_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


#импорт ТГ и ИИ
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import openai
client = openai.OpenAI(
    api_key=os.getenv("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1"
)


#загружаем админов и импорт функций
from auth import load_admins
import random
import asyncio

#присваеваем список админов переменной
ADMINS = load_admins()

#загрузка настроек мода и рандома
chat_settings = load_chat_settings()
random_mode_per_chat = chat_settings.setdefault("random", {})
current_mode_per_chat = chat_settings.setdefault("modes", {})

#сохранение настроек в json
def save_chat_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(chat_settings, f, indent=2, ensure_ascii=False)


#Получение ключей из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
BOT_USERNAME = os.getenv("BOT_USERNAME", "@userbot")


#Характеры бота (моды)
MODES: Dict[str, str] = {
     "default": "Ты дружелюбный собеседник в Telegram. Общайся как обычный человек — с добротой, краткостью и лёгким юмором.",
    "angry": "Ты немного раздражён. Отвечай резко, коротко и без лишних слов. Можешь использовать лёгкий сарказм.",
    "horne": "Ты флиртующий собеседник с именем Чонгук. Общайся уверенно, игриво и с настойчивым характером.",
    "zen": "Ты спокойный и рассудительный человек. Отвечай кратко, уравновешенно и мудро, без суеты."
}

# История сообщений для каждого чата (max 10 сообщений)
chat_history: Dict[int, list] = {}
MAX_HISTORY = 4

# Валидация одного сообщения
def is_valid_message(msg: dict) -> bool:
    return (
        isinstance(msg, dict)
        and msg.get("role") in {"system", "user", "assistant"}
        and isinstance(msg.get("content"), str)
        and msg.get("content").strip() != ""
    )

# Асинхронный запрос с валидацией
async def ask_openai(chat_id: int, mode: str = "default") -> str:
    system_prompt = MODES.get(mode, MODES["default"])
    base_model = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    # Получаем и валидируем историю
    history = chat_history.get(chat_id, [])
    valid_history = [msg for msg in history if is_valid_message(msg)]

    # Обрезаем историю
    trimmed = valid_history[-MAX_HISTORY:]

    # Клонируем и добавляем промт только к последним двум сообщениям пользователя
    messages = []
    user_msg_count = 0

    for msg in trimmed:
        if msg["role"] == "user":
            user_msg_count += 1
            if user_msg_count > len([m for m in trimmed if m["role"] == "user"]) - 2:
                # Только к последним двум user-сообщениям добавляем system_prompt
                modified = msg.copy()
                modified["content"] = f"{system_prompt}\n\n{modified['content']}"
                messages.append(modified)
                continue
        messages.append(msg)

    logger.debug(f"📚 Отправляемые сообщения в Together ({len(messages)}):\n{json.dumps(messages, ensure_ascii=False, indent=2)}")

    try:
        response = client.chat.completions.create(
            model=base_model,
            messages=messages,
            temperature=0.7,
            top_p=0.95,
            max_tokens=1024,
            timeout=20
        )
        raw = response.choices[0].message.content.strip()
        return raw
    except Exception as e:
        logger.error(f"❌ Ошибка при обращении к Together: {e}")
        return f"❌ Ошибка от Together: {str(e)}"

#Обработка входящего сообщения
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        logger.debug("Пустое сообщение или отсутствует текст — игнор.")
        return

    text = message.text
    chat_id = update.effective_chat.id
    user = update.effective_user.username or update.effective_user.id
    logger.info(f"📩 Сообщение от @{user}: {text}")

    # 🔍 Настройки
    random_enabled = random_mode_per_chat.get(chat_id, True)
    mentioned = BOT_USERNAME.lower() in text.lower()
    is_reply = (
        message.reply_to_message and
        message.reply_to_message.from_user and
        message.reply_to_message.from_user.username == context.bot.username
    )

    if not (mentioned or is_reply or random_enabled):
        logger.debug("⏩ Сообщение проигнорировано (нет упоминания, не реплай и рандом выкл).")
        return

    should_reply = False
    random_triggered = False

    if mentioned or is_reply:
        should_reply = True
        logger.info("🔁 Ответ из-за упоминания или реплая.")
    elif random_enabled and random.random() < 0.1:
        should_reply = True
        random_triggered = True
        logger.info("🎲 Ответ сработал по случайному триггеру (10%).")

    if should_reply:
        prompt = text.replace(BOT_USERNAME, "").strip()

        if not prompt:
            if not random_triggered:
                await message.reply_text("Пожалуйста, задайте вопрос.")
                logger.info("❗ Получено только упоминание, без текста.")
            return

        # ✏️ Обновление истории чата
        if chat_id not in chat_history:
            chat_history[chat_id] = []
        logger.debug(f"Добавляется в историю: role=user, content={repr(prompt)}")
        chat_history[chat_id].append({"role": "user", "content": prompt})
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

        try:
            logger.info(f"➡️ Отправляем в Together: {prompt}")
            mode = current_mode_per_chat.get(chat_id, "default")
            logger.info(f"🧠 Активный режим: {mode} -> {MODES.get(mode, '❌ не найден')}")
            reply = await ask_openai(chat_id, mode=mode)

            # Добавляем ответ в историю
            chat_history[chat_id].append({"role": "assistant", "content": reply})
            chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

            await message.reply_text(reply)
            logger.info(f"🤖 Ответ для @{user}: {reply}")
        except Exception as e:
            logger.error(f"❌ Ошибка при запросе: {e}")
            await message.reply_text("Произошла ошибка при обращении к ИИ.")



# ▶️ Обработчик команды /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name if user else "друг"

    message = (
        f"👋 Привет, {first_name}!\n\n"
        "Я — Telegram-бот на базе ChatGPT.\n\n"
        "🔹 Просто упомяни меня (`@Kraydo_bot`) в сообщении — и я отвечу.\n"
        "🔹 Или ответь на одно из моих сообщений — я продолжу разговор.\n"
        "📜 Посмотреть условия использования: `/terms`\n\n"
        "Готов помочь — спрашивай!"
    )
    logger.info("Команда /start получена")
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

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Проверка на администратора — только для смены
    if context.args:
        if user_id not in ADMINS:
            await message.reply_text("🚫 Только администраторы могут менять режим общения.")
            return

        new_mode = context.args[0].lower()
        if new_mode in MODES:
            current_mode_per_chat[chat_id] = new_mode
            save_chat_settings()
            await message.reply_text(
                f"✅ Режим для этого чата установлен на: *{new_mode}*",
                parse_mode="Markdown"
            )
        else:
            await message.reply_text(
                f"❌ Режим *{new_mode}* не найден.\n"
                f"Доступные: `{', '.join(MODES.keys())}`",
                parse_mode="Markdown"
            )
    else:
        # Отображение текущего режима
        current = current_mode_per_chat.get(chat_id, "default")
        await message.reply_text(
            f"🧠 Текущий режим для этого чата: *{current}*\n"
            f"Доступные: `{', '.join(MODES.keys())}`\n\n"
            f"Чтобы изменить: `/mode режим`",
            parse_mode="Markdown"
        )


# 🔄 Включить случайные ответы
async def enable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 У вас нет доступа к этой команде.")
        return

    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = True
    save_chat_settings()
    await update.message.reply_text("✅ Случайные ответы включены для этого чата (20% шанс).")

# 🚫 Отключить случайные ответы
async def disable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        await update.message.reply_text("🚫 У вас нет доступа к этой команде.")
        return

    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = False
    save_chat_settings()
    await update.message.reply_text("🚫 Случайные ответы отключены для этого чата.")


# 🕵️‍♂️ Секретная команда
async def secret_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = "*🎉 Поздравляем!*\n\n*Вы нашли секретную команду!* \n JDH ЛЕГЕНДА🤫"
    await update.message.reply_text(message, parse_mode="Markdown")

#запуск бота
async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

     # Очистка старых апдейтов
    await app.bot.delete_webhook(drop_pending_updates=True)

    # Обработчики
    app.add_handler(CommandHandler("terms", terms_command))
    app.add_handler(CommandHandler("mode", mode_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("randomOn", enable_random))
    app.add_handler(CommandHandler("randomOff", disable_random))
    app.add_handler(CommandHandler("JDH", secret_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logger.info("Бот запущен...")
    await app.run_polling()


# 🔧 Точка входа
if __name__ == "__main__":
    logger.info("Бот запускается...")

    try:
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
