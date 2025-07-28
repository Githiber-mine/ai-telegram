ADMIN_ID = 7029603268  # 🔁 Замени на свой Telegram user ID

async def notify_admin(bot, text: str):
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Ошибка отправки админу {ADMIN_ID}: {e}")
