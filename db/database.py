import asyncpg
from utils.history import current_mode_per_chat, random_mode_per_chat
from config import DATABASE_URL

async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_settings (
            chat_id BIGINT PRIMARY KEY,
            mode TEXT DEFAULT 'default',
            random_enabled BOOLEAN DEFAULT TRUE
        );
    """)
    await conn.close()

async def load_chat_settings():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT chat_id, mode, random_enabled FROM chat_settings")
    for row in rows:
        current_mode_per_chat[row["chat_id"]] = row["mode"]
        random_mode_per_chat[row["chat_id"]] = row["random_enabled"]
    await conn.close()

async def save_chat_setting(chat_id: int):
    mode = current_mode_per_chat.get(chat_id, "default")
    random_enabled = random_mode_per_chat.get(chat_id, True)

    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO chat_settings (chat_id, mode, random_enabled)
        VALUES ($1, $2, $3)
        ON CONFLICT (chat_id) DO UPDATE
        SET mode = EXCLUDED.mode, random_enabled = EXCLUDED.random_enabled
    """, chat_id, mode, random_enabled)
    await conn.close()
