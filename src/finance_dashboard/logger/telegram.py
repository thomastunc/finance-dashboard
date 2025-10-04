import logging
import os

import requests

from finance_dashboard.logger import Logger


class TelegramLogger(Logger):
    """Logger that sends error messages to Telegram in addition to file logging."""

    def __init__(self, log_file_name=None, bot_token="", chat_id="", telegram_log_level=logging.ERROR):
        # Get log level from environment for file logging
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        file_log_level = getattr(logging, log_level_str, logging.INFO)

        super().__init__(log_file_name, file_log_level)
        self.bot_token = bot_token
        self.chat_id = chat_id

        # Only add Telegram handler if credentials are provided
        if bot_token and chat_id:
            telegram_handler = self.TelegramHandler(bot_token, chat_id)
            formatter = logging.Formatter("%(levelname)s - %(name)s\n\n%(message)s")

            telegram_handler.setFormatter(formatter)
            telegram_handler.setLevel(telegram_log_level)  # Keep Telegram on ERROR level

            self.log.addHandler(telegram_handler)

    class TelegramHandler(logging.Handler):
        def __init__(self, bot_token, chat_id):
            super().__init__()
            self.bot_token = bot_token
            self.chat_id = chat_id

        def emit(self, record):
            """Send log record to Telegram."""
            log_entry = self.format(record)

            requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                params={
                    "chat_id": self.chat_id,
                    "text": log_entry,
                },
                timeout=10,
            )
