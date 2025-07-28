def is_valid_message(text: str) -> bool:
    return isinstance(text, str) and 0 < len(text.strip()) <= 2000
