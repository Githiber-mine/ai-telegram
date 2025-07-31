# core/handlers.py

import random
import re
from telegram import Update
from telegram.ext import ContextTypes
from core.modes import MODES
from config import BOT_USERNAME, MAX_HISTORY, ADMINS
from core.ai import ask_openai
from utils.history import chat_history, current_mode_per_chat, random_mode_per_chat
from utils.logger import logger
from utils.validator import is_valid_message
from db.database import save_chat_setting

# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я ИИ-бот. Просто напиши мне, или упомяни меня в чате.")

# Команда /terms
async def terms_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💡 Условия использования: не вводите личную информацию. Ответы генерируются ИИ.")

# Команда /mode
async def mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if context.args:
        if user_id not in ADMINS:
            await message.reply_text("🚫 Только администраторы могут менять режим общения.")
            return

        new_mode = context.args[0].lower()
        if new_mode in MODES:
            current_mode_per_chat[chat_id] = new_mode
            chat_history[chat_id] = []  # ⬅️ ОЧИСТКА истории при смене режима
            await save_chat_setting(chat_id)
            await message.reply_text(
                f"✅ Режим для этого чата установлен на: *{new_mode}*\n"
                f"🧹 История чата была очищена.",
                parse_mode="Markdown"
            )
        else:
            await message.reply_text(
                f"❌ Режим *{new_mode}* не найден.\n"
                f"Доступные: `{', '.join(MODES.keys())}`",
                parse_mode="Markdown"
            )
    else:
        current = current_mode_per_chat.get(chat_id, "default")
        await message.reply_text(
            f"🧠 Текущий режим для этого чата: *{current}*\n"
            f"Доступные: `{', '.join(MODES.keys())}`\n\n"
            f"Чтобы изменить: `/mode режим`",
            parse_mode="Markdown"
        )

# Команды /randomOn и /randomOff
async def enable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = True
    await save_chat_setting(chat_id)
    await update.message.reply_text("✅ Случайные ответы включены.")

async def disable_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    random_mode_per_chat[chat_id] = False
    await save_chat_setting(chat_id)
    await update.message.reply_text("❌ Случайные ответы отключены.")

# Пасхальная команда
async def secret_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔒 Поздравляю! Ты нашёл пасхалку 👀")

# Обработка обычных сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not is_valid_message(message.text):
        logger.debug("Пустое сообщение или отсутствует текст — игнор.")
        return

    text = message.text.strip()
    chat_id = update.effective_chat.id
    user = update.effective_user.username or update.effective_user.id
    logger.info(f"📩 Сообщение от @{user}: {text}")

    random_enabled = random_mode_per_chat.get(chat_id, True)
    mentioned = BOT_USERNAME.lower() in text.lower()
    is_reply = (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == context.bot.id
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

        if chat_id not in chat_history:
            chat_history[chat_id] = []

        # 👇 Добавляем имя только в группах
        name = None
        if update.effective_chat.type in ("group", "supergroup"):
            name = update.effective_user.first_name or update.effective_user.username or "Пользователь"

        logger.debug(f"Добавляется в историю: role=user, name={name}, content={repr(prompt)}")
        chat_history[chat_id].append({
            "role": "user",
            "content": prompt,
            **({"name": name} if name else {})
        })
        chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]

        # 🔽 Ограничение по количеству слов
        MAX_WORDS_PER_MESSAGE = 150
        MAX_TOTAL_WORDS = 1500

        def total_words(messages):
            return sum(len(m.get("content", "").split()) for m in messages)

        # Удаляем старые сообщения, если отдельные слишком длинные или история слишком объёмная
        while chat_history[chat_id] and (
            any(len(m.get("content", "").split()) > MAX_WORDS_PER_MESSAGE for m in chat_history[chat_id])
            or total_words(chat_history[chat_id]) > MAX_TOTAL_WORDS
        ):
            removed = chat_history[chat_id].pop(0)
            logger.debug(f"🧹 Удалено сообщение из истории из-за длины: {removed}")

        try:
            logger.info(f"➡️ Отправляем в Together: {prompt}")
            mode = current_mode_per_chat.get(chat_id, "default")
            logger.info(f"🧠 Активный режим: {mode} -> {MODES.get(mode, '❌ не найден')}")
            reply = await ask_openai(chat_id, mode=mode)

            reply = clean_ai_reply(reply)

            if not reply or len(reply) > 1000:
                logger.warning("⚠️ Ответ ИИ некорректный или слишком длинный.")
                await message.reply_text("⚠️ Произошла ошибка генерации. Пожалуйста, переформулируйте вопрос.")
                return

            # ⛔ Не добавляем имя в ответ ИИ
            chat_history[chat_id].append({
                "role": "assistant",
                "content": reply
            })
            chat_history[chat_id] = chat_history[chat_id][-MAX_HISTORY:]
            logger.debug("✅ Ответ ИИ добавлен в историю.")
            await message.reply_text(reply)
            logger.info(f"🤖 Ответ для @{user}: {reply}")

        except Exception as e:
            logger.error(f"❌ Ошибка при запросе: {e}")
            await message.reply_text("Произошла ошибка при обращении к ИИ.")

# Фильтр-очистка вложенных диалогов
def clean_ai_reply(reply: str) -> str:
    stop_phrases = [
        r"^\s*(ИИ|user|assistant|пользователь):",
        r"сейчас мне нужно ответить на вопрос",
        r"вот пример",
        r"пример кода",
        r"код:",
        r"1\.\s",
    ]

    lines = reply.splitlines()
    cleaned = []

    for line in lines:
        if any(re.search(p, line.strip(), re.IGNORECASE) for p in stop_phrases):
            break
        cleaned.append(line)

    return "\n".join(cleaned).strip()
