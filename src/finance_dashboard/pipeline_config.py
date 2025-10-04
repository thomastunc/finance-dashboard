"""Pipeline configuration management for Finance Dashboard.

Handles loading and parsing YAML pipeline configurations.
"""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()


class PipelineConfig:
    """Pipeline configuration loaded from YAML file."""

    def __init__(self, config_path: str):
        """Initialize pipeline config from YAML file.

        Args:
            config_path: Path to the pipeline YAML configuration file

        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Pipeline configuration not found: {config_path}")

        with Path.open(self.config_path) as f:
            self._config = yaml.safe_load(f)

        if not self._config:
            raise ValueError(f"Empty or invalid YAML configuration: {config_path}")

    def _get_env_value(self, env_var_name: str, default: str = "") -> str:
        """Get value from environment variable.

        Args:
            env_var_name: Name of the environment variable
            default: Default value if env var is not set

        Returns:
            Environment variable value or default

        """
        return os.getenv(env_var_name, default)

    # Global Configuration
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self._config.get("global", {}).get("log_level", "INFO")

    @property
    def preferred_currency(self) -> str:
        """Get preferred currency."""
        return self._config.get("global", {}).get("preferred_currency", "EUR")

    # Database Configuration
    @property
    def database_connector(self) -> str:
        """Get database connector type."""
        return self._config.get("database", {}).get("connector", "bigquery")

    @property
    def database_credentials_path(self) -> str:
        """Get database credentials path."""
        return self._config.get("database", {}).get("credentials_path", "config/service_account.json")

    @property
    def database_project_id(self) -> str:
        """Get database project ID."""
        return self._config.get("database", {}).get("project_id", "")

    @property
    def database_schema_id(self) -> str:
        """Get database schema ID."""
        return self._config.get("database", {}).get("schema_id", "")

    @property
    def database_location(self) -> str:
        """Get database location."""
        return self._config.get("database", {}).get("location", "europe-west4")

    @property
    def table_names(self) -> dict[str, str]:
        """Get table names configuration."""
        return self._config.get("database", {}).get(
            "table_names", {"accounts": "bank-accounts", "stocks": "stocks", "crypto": "crypto", "total": "total"}
        )

    # Logging Configuration
    @property
    def logging_type(self) -> str:
        """Get logging type (telegram, console, file)."""
        return self._config.get("logging", {}).get("type", "console")

    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token from environment."""
        env_var = self._config.get("logging", {}).get("telegram", {}).get("bot_token_env", "")
        return self._get_env_value(env_var)

    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID from environment."""
        env_var = self._config.get("logging", {}).get("telegram", {}).get("chat_id_env", "")
        return self._get_env_value(env_var)

    @property
    def telegram_send_summary(self) -> bool:
        """Get Telegram send summary flag."""
        return self._config.get("logging", {}).get("telegram", {}).get("send_summary", False)

    @property
    def telegram_dashboard_url(self) -> str:
        """Get Telegram dashboard URL."""
        return self._config.get("logging", {}).get("telegram", {}).get("dashboard_url", "")

    # Bank Configuration
    @property
    def bank_enabled(self) -> bool:
        """Check if bank collection is enabled."""
        return self._config.get("bank", {}).get("enabled", False)

    @property
    def bank_accounts(self) -> list[dict[str, Any]]:
        """Get list of bank account configurations."""
        return self._config.get("bank", {}).get("accounts", [])

    # Stock Configuration
    @property
    def stock_enabled(self) -> bool:
        """Check if stock collection is enabled."""
        return self._config.get("stock", {}).get("enabled", False)

    @property
    def stock_accounts(self) -> list[dict[str, Any]]:
        """Get list of stock account configurations."""
        return self._config.get("stock", {}).get("accounts", [])

    # Crypto Configuration
    @property
    def crypto_enabled(self) -> bool:
        """Check if crypto collection is enabled."""
        return self._config.get("crypto", {}).get("enabled", False)

    @property
    def crypto_coinmarketcap_api_key(self) -> str:
        """Get CoinMarketCap API key from environment."""
        env_var = self._config.get("crypto", {}).get("coinmarketcap_api_key_env", "")
        return self._get_env_value(env_var)

    @property
    def crypto_moralis_api_key(self) -> str:
        """Get Moralis API key from environment."""
        env_var = self._config.get("crypto", {}).get("moralis_api_key_env", "")
        return self._get_env_value(env_var)

    @property
    def crypto_accounts(self) -> list[dict[str, Any]]:
        """Get list of crypto account configurations."""
        return self._config.get("crypto", {}).get("accounts", [])

    def get_account_env_value(self, account_config: dict[str, Any], key: str, default: str = "") -> str:
        """Get environment value for a specific account configuration key.

        Args:
            account_config: Account configuration dictionary
            key: Key to look up (should end with '_env')
            default: Default value if not found

        Returns:
            Environment variable value or default

        """
        env_var = account_config.get(key, "")
        if not env_var:
            return default
        return self._get_env_value(env_var, default)

    def validate(self) -> list[str]:
        """Validate pipeline configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)

        """
        errors = []

        # Validate database configuration
        if not self.database_project_id:
            errors.append("Database project ID not configured in pipeline YAML")

        if not self.database_schema_id:
            errors.append("Database schema ID not configured in pipeline YAML")

        # Validate at least one data source is enabled
        if not (self.bank_enabled or self.stock_enabled or self.crypto_enabled):
            errors.append("No data sources enabled (enable at least bank, stock, or crypto)")

        # Validate bank accounts if enabled
        if self.bank_enabled and not self.bank_accounts:
            errors.append("Bank collection enabled but no accounts configured")

        # Validate stock accounts if enabled
        if self.stock_enabled and not self.stock_accounts:
            errors.append("Stock collection enabled but no accounts configured")

        # Validate crypto accounts if enabled
        if self.crypto_enabled and not self.crypto_accounts:
            errors.append("Crypto collection enabled but no accounts configured")

        return errors
