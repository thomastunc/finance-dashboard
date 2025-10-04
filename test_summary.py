"""Test script to test the daily summary feature without running the full data collection."""

from finance_dashboard.config import AppConfig


def test_daily_summary():
    """Test the daily summary feature."""
    config = AppConfig()
    logger = config.logger

    if not config.telegram.bot_token or not config.telegram.chat_id:
        return

    if not config.telegram.send_summary:
        return

    try:
        summary_data = config.connector.get_daily_summary()

        if not summary_data:
            return

        logger.send_daily_summary(
            summary_data, dashboard_url=config.telegram.dashboard_url, currency=config.preferred_currency
        )

    except Exception:
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_daily_summary()
