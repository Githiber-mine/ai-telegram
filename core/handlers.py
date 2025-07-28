from telegram import Update
from telegram.ext import ContextTypes
from utils.logger import logger
from utils.history import chat_history, current_mode_per_chat, random_mode_per_chat
from utils.cleaner import clean_ai_reply
from core.ai import ask_openai
from config import MAX_HISTORY, BOT_USERNAME, ADMINS
import random

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я — ИИ-бот. Напиши что-нибудь!")

async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❗ Используя этого бота, вы соглашаетесь с политикой конфиденциальности и условиями использования.")

async def secret_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ты нашёл секретный режим!")

async def enable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = True
    await update.message.reply_text("🎲 Случайные ответы включены!")

async def disable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = False
    await update.message.reply_text("🔕 Случайные ответы отключены!")

async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if context.args:
        if user_id not in ADMINS:
            await message.reply_text("🚫 Только администраторы могут менять режим общения.")
            return

        new_mode = context.args[0].lower()
        current_mode_per_chat[chat_id] = new_mode
        await message.reply_text(f"✅ Режим установлен: *{new_mode}*", parse_mode="Markdown")
    else:
        current = current_mode_per_chat.get(chat_id, "default")
        await message.reply_text(f"🧠 Текущий режим: *{current}*", parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user.username or update.effective_user.id
    text = message.text.strip()

    logger.info(f"📩 Сообщение от @{user}: {text}")

    mentioned = BOT_USERNAME.lower() in text.lower()
    is_reply = message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == context.bot.id
    random_enabled = random_mode_per_chat.get(chat_id, True)

    should_reply = mentioned or is_reply or (random_enabled and random.random() < 0.1)
    if not should_reply:
        return

    prompt = text.replace(BOT_USERNAME, "").strip()
    if not prompt:
        await message.reply_text("❗ Пожалуйста, задай вопрос.")
        return

    chat_history.setdefault(chat_id, []).append({"role": "user", "content": prompt})
    chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

    try:
        mode = current_mode_per_chat.get(chat_id, "default")
        logger.info(f"🧠 Активный режим: {mode}")
        reply = await ask_openai(chat_id, mode=mode)
        reply = clean_ai_reply(reply)

        if not reply or len(reply) > 1000:
            await message.reply_text("⚠️ Ошибка генерации ответа.")
            return

        chat_history[chat_id].append({"role": "assistant", "content": reply})
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]
        await message.reply_text(reply)
    except Exception as e:
        logger.error(f"Ошибка при генерации ответа: {e}")
        await message.reply_text("Произошла ошибка при обращении к ИИ.")
