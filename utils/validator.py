def is_valid_message(msg: dict) -> bool:
    content = msg.get("content", "")
    return (
        isinstance(msg, dict)
        and msg.get("role") in {"system", "user", "assistant"}
        and isinstance(content, str)
        and 0 < len(content.strip()) <= 2000
    )
