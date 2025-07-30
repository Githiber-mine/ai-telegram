from together import Together
from core.modes import MODES
from config import TOGETHER_API_KEY, MAX_HISTORY
from utils.validator import is_valid_message
from utils.history import chat_history


# Асинхронный запрос с валидацией
client = Together(api_key=TOGETHER_API_KEY)
BASE_MODEL = "mistralai/Mixtral-8x7B-Instruct-v0.1"
MAX_CHARS = 4000

async def ask_openai(chat_id: int, mode: str = "default") -> str:
    system_prompt = MODES.get(mode, MODES["default"]).strip()
    raw_history = chat_history.get(chat_id, [])
    valid_history = [m for m in raw_history if is_valid_message(m.get("content"))]
    trimmed = valid_history[-MAX_HISTORY:]

    messages = [{"role": "system", "content": system_prompt}]

    for msg in trimmed:
        role = msg.get("role")
        content = msg.get("content", "").strip()
        if not content:
            continue  # Пропускаем пустое сообщение
        name = msg.get("name", "Пользователь")

        if role == "user":
            messages.append({"role": "user", "content": f"{name}: {content}"})
        elif role == "assistant":
            messages.append({"role": "assistant", "content": content})

    try:
        response = client.chat.completions.create(
            model=BASE_MODEL,
            messages=messages,
            temperature=0.7,
            top_p=0.95,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Ошибка от Together: {str(e)}"
