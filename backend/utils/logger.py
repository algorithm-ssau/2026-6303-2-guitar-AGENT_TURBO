"""Настройка логирования для Guitar Agent."""

import logging


def get_logger(name: str = "guitar-agent") -> logging.Logger:
    """Создаёт и возвращает настроенный логгер.

    Формат: [timestamp] LEVEL: message
    Уровень по умолчанию: INFO
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(levelname)s: %(message)s"
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
