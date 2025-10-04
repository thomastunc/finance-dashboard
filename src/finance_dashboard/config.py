"""Configuration management for the Finance Dashboard application.

Centralizes environment variable loading and validation.
"""

import os
from dataclasses import dataclass

from currency_converter import CurrencyConverter
from dotenv import load_dotenv

from finance_dashboard.connector.bigquery import BigQueryConnector
from finance_dashboard.logger.telegram import TelegramLogger

load_dotenv()


@dataclass
class DatabaseConfig:
    """BigQuery database configuration."""

    credentials_path: str
    project_id: str
    schema_id: str
    location: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create DatabaseConfig from environment variables."""
        return cls(
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
            project_id=os.getenv("PROJECT_ID", ""),
            schema_id=os.getenv("SCHEMA_ID", ""),
            location=os.getenv("LOCATION", ""),
        )


@dataclass
class TelegramConfig:
    """Telegram logger configuration."""

    bot_token: str
    chat_id: str

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """Create TelegramConfig from environment variables."""
        return cls(bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""), chat_id=os.getenv("TELEGRAM_CHAT_ID", ""))


@dataclass
class BunqConfig:
    """Bunq API configuration."""

    api_key: str
    configuration_file: str

    @classmethod
    def from_env(cls) -> "BunqConfig":
        """Create BunqConfig from environment variables."""
        return cls(
            api_key=os.getenv("BUNQ_API_KEY", ""),
            configuration_file=os.getenv("BUNQ_CONFIGURATION_FILE_PROD", ""),
        )


@dataclass
class DeGiroConfig:
    """DeGiro API configuration."""

    username: str
    password: str
    int_account: str
    totp: str

    @classmethod
    def from_env(cls) -> "DeGiroConfig":
        """Create DeGiroConfig from environment variables."""
        return cls(
            username=os.getenv("DEGIRO_USERNAME", ""),
            password=os.getenv("DEGIRO_PASSWORD", ""),
            int_account=os.getenv("DEGIRO_INT_ACCOUNT", ""),
            totp=os.getenv("DEGIRO_TOTP", ""),
        )


class AppConfig:
    """Main application configuration."""

    def __init__(self):
        self.database = DatabaseConfig.from_env()
        self.telegram = TelegramConfig.from_env()
        self.bunq = BunqConfig.from_env()
        self.degiro = DeGiroConfig.from_env()

        self.preferred_currency = os.getenv("PREFERRED_CURRENCY", "EUR")
        self.coinmarketcap_api_key = os.getenv("COINMARKETCAP_API_KEY", "")
        self.moralis_api_key = os.getenv("MORALIS_API_KEY", "")
        self.coinbase_key_file = os.getenv("COINBASE_KEY_FILE", "")

        # Wallet addresses
        self.metamask_wallet = os.getenv("METAMASK_WALLET_ADDRESS", "")
        self.coinbase_wallet = os.getenv("COINBASE_WALLET_ADDRESS", "")
        self.helium_wallet = os.getenv("HELIUM_WALLET_ADDRESS", "")

        # BigQuery table names
        self.bq_account_name = os.getenv("BQ_ACCOUNT_NAME", "")
        self.bq_stock_name = os.getenv("BQ_STOCK_NAME", "")
        self.bq_crypto_name = os.getenv("BQ_CRYPTO_NAME", "")

        # Create component instances
        self._setup_components()

    def _setup_components(self):
        """Initialize the main application components."""
        self.connector = BigQueryConnector(
            self.database.credentials_path,
            self.database.project_id,
            self.database.schema_id,
            self.database.location,
        )

        self.converter = CurrencyConverter(ref_currency=self.preferred_currency)

        self.logger = TelegramLogger(
            None,  # Use default daily log file naming
            self.telegram.bot_token,
            self.telegram.chat_id,
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of missing required fields."""
        missing = []

        required_fields = {
            "Database Project ID": self.database.project_id,
            "Database Schema ID": self.database.schema_id,
            "Preferred Currency": self.preferred_currency,
        }

        for field_name, value in required_fields.items():
            if not value or value.strip() == "":
                missing.append(field_name)

        return missing

    def to_legacy_config(self) -> dict:
        """Convert to legacy config format for backward compatibility."""
        return {
            "connector": self.connector,
            "converter": self.converter,
            "logger": self.logger,
            "coinmarketcap_api_key": self.coinmarketcap_api_key,
        }
