import aiosqlite
from config import DB_PATH
from utils.history import current_mode_per_chat, random_mode_per_chat

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                mode TEXT DEFAULT 'default',
                random INTEGER DEFAULT 1
            )
        ''')
        await db.commit()

async def load_chat_settings():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT chat_id, mode, random FROM chat_settings") as cursor:
            async for chat_id, mode, random_value in cursor:
                current_mode_per_chat[chat_id] = mode
                random_mode_per_chat[chat_id] = bool(random_value)

async def save_chat_setting(chat_id: int, mode: str, random: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO chat_settings (chat_id, mode, random)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET mode = excluded.mode, random = excluded.random
        """, (chat_id, mode, int(random)))
        await db.commit()
