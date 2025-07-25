import json

def load_admins(path="admins.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("admins", []))
    except FileNotFoundError:
        return set()
