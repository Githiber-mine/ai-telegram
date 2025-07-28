from together import Together
from utils.history import chat_history




# Асинхронный запрос с валидацией
async def ask_openai(chat_id: int, mode: str = "default") -> str:
    system_prompt = MODES.get(mode, MODES["default"])
    base_model = "mistralai/Mistral-7B-Instruct-v0.2"
    max_chars = 4000  # ⛔️ Ограничение по длине prompt (в символах)

    # Получаем и валидируем историю
    raw_history = chat_history.get(chat_id, [])
    valid_history = [msg for msg in raw_history if is_valid_message(msg)]
    trimmed = valid_history[-MAX_HISTORY:]

    # Сборка промта вручную
    prompt_parts = [system_prompt.strip(), ""]
    for msg in trimmed:
        role = msg["role"]
        content = msg["content"].strip()

        if role == "user":
            prompt_parts.append(f"Пользователь: {content}")
        elif role == "assistant":
            prompt_parts.append(f"ИИ: {content}")

    prompt_parts.append("ИИ:")
    full_prompt = "\n".join(prompt_parts).strip()

    # ✅ Ограничение по длине
    if len(full_prompt) > max_chars:
        full_prompt = full_prompt[-max_chars:]  # обрезаем с начала, оставляя концовку

    try:
        response = client.completions.create(
            model=base_model,
            prompt=full_prompt,
            temperature=0.7,
            top_p=0.95,
            max_tokens=512
        )
        return response.choices[0].text.strip()
    except Exception as e:
        return f"❌ Ошибка от Together: {str(e)}"
