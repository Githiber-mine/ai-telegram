import re

def clean_ai_reply(reply: str) -> str:
    reply = re.sub(r"\*\*(.*?)\*\*", r"\1", reply)
    reply = re.sub(r"__(.*?)__", r"\1", reply)
    reply = re.sub(r"\*(.*?)\*", r"\1", reply)
    reply = re.sub(r"_([^_]+)_", r"\1", reply)
    return reply.strip()
