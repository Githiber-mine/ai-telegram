# core/ai.py
from utils.history import chat_history

async def ask_openai(chat_id: int, mode: str = "default") -> str:
    messages = chat_history.get(chat_id, [])
    system_prompt = f"Режим: {mode}"
    payload = [
        {"role": "system", "content": system_prompt},
        *messages
    ]
    # Здесь добавь API-запрос к Together / OpenAI — заменено заглушкой
    return "Пример ответа от ИИ (заглушка)"
