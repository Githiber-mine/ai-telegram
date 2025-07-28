def is_valid_message(message: str) -> bool:
    return bool(message and len(message.strip()) > 0)
