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

    def send_message(self, message: str, parse_mode: str = "HTML"):
        """Send a message to Telegram.

        Args:
            message: The message text to send
            parse_mode: Message formatting mode ('HTML' or 'Markdown')

        """
        if not self.bot_token or not self.chat_id:
            self.log.warning("Cannot send Telegram message: bot_token or chat_id not configured")
            return

        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                params={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": False,
                },
                timeout=10,
            )
            response.raise_for_status()
        except Exception:
            self.log.exception("Failed to send Telegram message")

    def send_daily_summary(self, summary_data: dict, dashboard_url: str = "", currency: str = "EUR"):
        """Send a formatted daily summary to Telegram.

        Args:
            summary_data: Dictionary with summary data from BigQueryConnector.get_daily_summary()
            dashboard_url: Optional URL to the dashboard
            currency: Currency symbol to display

        """
        if not summary_data:
            self.send_message("📊 No data available for today")
            return

        # Emojis for visual representation
        total_emoji = "💰" if summary_data["total_change"] >= 0 else "📉"

        # Build the message
        message_parts = ["<b>📊 Daily Summary</b>\n"]

        # Total section - simplified format
        message_parts.append(
            f"{total_emoji} <b>{os.getenv('BQ_TOTAL_NAME', 'total')}: </b> €{summary_data['total_today']:,.0f}".replace(
                ",", "."
            )
        )

        # Change indicator with emoji symbols
        change_emoji = "▲" if summary_data["total_change"] >= 0 else "🔻"
        message_parts.append(
            f"{change_emoji} €{abs(summary_data['total_change']):,.0f} "
            f"({summary_data['total_change_pct']:+.2f}%)\n".replace(",", ".")
        )

        category_emojis = {
            os.getenv("BQ_ACCOUNT_NAME", "bank-accounts"): "🏦",
            os.getenv("BQ_STOCK_NAME", "stocks"): "📈",
            os.getenv("BQ_CRYPTO_NAME", "crypto"): "🪙",
        }

        for cat in summary_data["categories"]:
            # Get emoji for category
            cat_emoji = category_emojis.get(cat["name"], "💼")
            cat_change_emoji = "▲" if cat["change"] >= 0 else "🔻"

            message_parts.append(f"{cat_emoji} <b>{cat['name']}:</b> €{cat['today']:,.0f}".replace(",", "."))

            message_parts.append(
                f"{cat_change_emoji} €{abs(cat['change']):,.0f} ({cat['change_pct']:+.2f}%)\n".replace(",", ".")
            )

        # Dashboard link
        if dashboard_url:
            message_parts.append(f'🔗 <a href="{dashboard_url}">Open Dashboard</a>')

        message = "\n".join(message_parts)
        self.send_message(message, parse_mode="HTML")

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
