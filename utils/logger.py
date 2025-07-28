import logging
import sys

# Настройки логгера
logger = logging.getLogger("telegram_openai_bot")
logger.setLevel(logging.INFO)

# Формат логов
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Лог только в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
