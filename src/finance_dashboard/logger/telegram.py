import logging
import requests

from finance_dashboard.logger import Logger


class TelegramLogger(Logger):
    def __init__(self, log_file_path, bot_token, chat_id, log_level=logging.ERROR):
        super().__init__(log_file_path)
        self.bot_token = bot_token
        self.chat_id = chat_id

        telegram_handler = self.TelegramHandler(bot_token, chat_id)
        formatter = logging.Formatter('%(levelname)s - %(name)s\n\n%(message)s')

        telegram_handler.setFormatter(formatter)
        telegram_handler.setLevel(log_level)

        self.log.addHandler(telegram_handler)

    class TelegramHandler(logging.Handler):
        def __init__(self, bot_token, chat_id):
            super().__init__()
            self.bot_token = bot_token
            self.chat_id = chat_id

        def emit(self, record):
            log_entry = self.format(record)

            requests.post(
                f'https://api.telegram.org/bot{self.bot_token}/sendMessage',
                params={
                    'chat_id': self.chat_id,
                    'text': log_entry,
                }
            )
