
import asyncpg
from config import DATABASE_URL
from utils.history import current_mode_per_chat, random_mode_per_chat

# Инициализация таблицы
async def init_db():
    async with asyncpg.connect(DATABASE_URL) as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id BIGINT PRIMARY KEY,
                mode TEXT DEFAULT 'default',
                random BOOLEAN DEFAULT TRUE
            )
        """)

# Загрузка всех настроек в память
async def load_chat_settings():
    async with asyncpg.connect(DATABASE_URL) as conn:
        rows = await conn.fetch("SELECT chat_id, mode, random FROM chat_settings")
        for row in rows:
            current_mode_per_chat[row["chat_id"]] = row["mode"]
            random_mode_per_chat[row["chat_id"]] = row["random"]

# Сохранение одной записи
async def save_chat_setting(chat_id: int):
    mode = current_mode_per_chat.get(chat_id, "default")
    random = random_mode_per_chat.get(chat_id, True)
    async with asyncpg.connect(DATABASE_URL) as conn:
        await conn.execute("""
            INSERT INTO chat_settings (chat_id, mode, random)
            VALUES ($1, $2, $3)
            ON CONFLICT (chat_id) DO UPDATE
            SET mode = EXCLUDED.mode, random = EXCLUDED.random
        """, chat_id, mode, random)
