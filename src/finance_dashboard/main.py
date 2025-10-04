"""Main Finance Dashboard application logic.

Orchestrates data collection from multiple sources based on pipeline configuration.
"""

import logging

from currency_converter import CurrencyConverter

from finance_dashboard.connector.bigquery import BigQueryConnector
from finance_dashboard.logger.telegram import TelegramLogger
from finance_dashboard.pipeline_config import PipelineConfig
from finance_dashboard.repository.bank.bunq_repository import BunqRepository
from finance_dashboard.repository.crypto.coinbase_repository import CoinbaseRepository
from finance_dashboard.repository.crypto.cosmos_repository import CosmosRepository
from finance_dashboard.repository.crypto.web3_repository import Web3Repository
from finance_dashboard.repository.stock.degiro_repository import DeGiroRepository


class FinanceDashboard:
    """Main application class for the Finance Dashboard."""

    def __init__(self, pipeline_config: PipelineConfig):
        """Initialize Finance Dashboard with pipeline configuration.

        Args:
            pipeline_config: Pipeline configuration loaded from YAML

        """
        self.config = pipeline_config
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self._setup_components()

        # Set up database schema on initialization
        self._setup_database()

    def _setup_components(self):
        """Initialize the main application components."""
        # Database connector
        self.connector = BigQueryConnector(
            self.config.database_credentials_path,
            self.config.database_project_id,
            self.config.database_schema_id,
            self.config.database_location,
        )

        # Currency converter
        self.converter = CurrencyConverter(ref_currency=self.config.preferred_currency)

        # Logger (Telegram if configured, otherwise console)
        if self.config.logging_type == "telegram" and self.config.telegram_bot_token:
            # Convert log level string to logging constant
            log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            self.telegram_logger = TelegramLogger(
                None,  # Use default daily log file naming
                self.config.telegram_bot_token,
                self.config.telegram_chat_id,
                log_level=log_level,
                table_names=self.config.table_names,
            )
        else:
            self.telegram_logger = None

        self.logger.info("Components initialized successfully")

    def _setup_database(self):
        """Ensure database schema (dataset, tables, and views) exists."""
        try:
            self.logger.info("Checking database setup")
            table_names = self.config.table_names
            self.connector.setup_database(
                table_names.get("accounts", "bank-accounts"),
                table_names.get("stocks", "stocks"),
                table_names.get("crypto", "crypto"),
            )
            self.logger.info("Database setup complete")
        except Exception as e:
            self.logger.warning(f"Database setup check failed: {e}")

    def _get_legacy_config(self) -> dict:
        """Create legacy config format for repositories.

        Returns:
            Dictionary with legacy configuration format

        """
        return {
            "connector": self.connector,
            "converter": self.converter,
            "logger": self.telegram_logger if self.telegram_logger else logging.getLogger(),
            "coinmarketcap_api_key": self.config.crypto_coinmarketcap_api_key,
        }

    def run(self):
        """Run all data collection processes based on pipeline configuration."""
        self.logger.info("=" * 60)
        self.logger.info("Starting Finance Dashboard data collection")
        self.logger.info("=" * 60)

        try:
            # Run each enabled data source
            if self.config.bank_enabled:
                self._collect_bank_data()

            if self.config.stock_enabled:
                self._collect_stock_data()

            if self.config.crypto_enabled:
                self._collect_crypto_data()

            self.logger.info("=" * 60)
            self.logger.info("Finance Dashboard data collection completed successfully")
            self.logger.info("=" * 60)

            # Send daily summary to Telegram if enabled
            self._send_daily_summary()

        except Exception:
            self.logger.exception("Finance Dashboard run failed")
            raise

    def _send_daily_summary(self):
        """Send daily summary to Telegram if enabled."""
        if not self.config.telegram_send_summary:
            self.logger.info("Telegram summary disabled - skipping")
            return

        if not self.telegram_logger:
            self.logger.info("Telegram not configured - skipping summary")
            return

        try:
            self.logger.info("Generating daily summary for Telegram")
            summary_data = self.connector.get_daily_summary()

            if summary_data:
                self.telegram_logger.send_daily_summary(
                    summary_data,
                    dashboard_url=self.config.telegram_dashboard_url,
                    currency=self.config.preferred_currency,
                )
                self.logger.info("Daily summary sent to Telegram successfully")
            else:
                self.logger.info("No summary data available")
        except Exception:
            self.logger.exception("Failed to send daily summary")

    # Bank Data Collection
    def _collect_bank_data(self):
        """Collect data from all configured bank accounts."""
        self.logger.info("-" * 60)
        self.logger.info("BANK ACCOUNTS")
        self.logger.info("-" * 60)

        for account_config in self.config.bank_accounts:
            account_name = account_config.get("name", "Unknown")
            account_type = account_config.get("type", "").lower()

            if account_type == "bunq":
                self._collect_bunq_account(account_name, account_config)
            else:
                self.logger.warning(f"Unknown bank account type: {account_type} for {account_name}")

    def _collect_bunq_account(self, account_name: str, account_config: dict):
        """Collect Bunq bank account data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary

        """
        api_key = self.config.get_account_env_value(account_config, "api_key_env")
        config_file = account_config.get("configuration_file", "")

        if not api_key:
            self.logger.info(f"Skipping {account_name} - no API key configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} account data")
            repository = BunqRepository(self._get_legacy_config(), api_key, config_file)
            repository.get_and_store_accounts(account_name)
            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")

    # Stock Data Collection
    def _collect_stock_data(self):
        """Collect data from all configured stock accounts."""
        self.logger.info("-" * 60)
        self.logger.info("STOCK ACCOUNTS")
        self.logger.info("-" * 60)

        for account_config in self.config.stock_accounts:
            account_name = account_config.get("name", "Unknown")
            account_type = account_config.get("type", "").lower()

            if account_type == "degiro":
                self._collect_degiro_account(account_name, account_config)
            else:
                self.logger.warning(f"Unknown stock account type: {account_type} for {account_name}")

    def _collect_degiro_account(self, account_name: str, account_config: dict):
        """Collect DeGiro stock data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary

        """
        username = self.config.get_account_env_value(account_config, "username_env")
        password = self.config.get_account_env_value(account_config, "password_env")
        int_account = self.config.get_account_env_value(account_config, "int_account_env")
        totp = self.config.get_account_env_value(account_config, "totp_env")

        if not username:
            self.logger.info(f"Skipping {account_name} - no credentials configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} stock data")
            repository = DeGiroRepository(self._get_legacy_config(), username, password, int_account, totp)
            repository.get_and_store_stocks(account_name)
            repository.get_and_store_account("Flatex")
            repository.logout()
            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")

    # Crypto Data Collection
    def _collect_crypto_data(self):
        """Collect data from all configured crypto accounts."""
        self.logger.info("-" * 60)
        self.logger.info("CRYPTO ACCOUNTS")
        self.logger.info("-" * 60)

        moralis_api_key = self.config.crypto_moralis_api_key

        for account_config in self.config.crypto_accounts:
            account_name = account_config.get("name", "Unknown")
            account_type = account_config.get("type", "").lower()

            if account_type == "coinbase":
                self._collect_coinbase_account(account_name, account_config)
            elif account_type == "web3":
                self._collect_web3_account(account_name, account_config, moralis_api_key)
            elif account_type == "web3-solana":
                self._collect_web3_solana_account(account_name, account_config, moralis_api_key)
            elif account_type == "cosmos":
                self._collect_cosmos_account(account_name, account_config)
            else:
                self.logger.warning(f"Unknown crypto account type: {account_type} for {account_name}")

    def _collect_coinbase_account(self, account_name: str, account_config: dict):
        """Collect Coinbase exchange data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary

        """
        key_file = account_config.get("key_file", "")

        if not key_file:
            self.logger.info(f"Skipping {account_name} - no key file configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} account data")
            repository = CoinbaseRepository(self._get_legacy_config(), key_file)
            repository.get_and_store_wallets(account_name)
            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")

    def _collect_web3_account(self, account_name: str, account_config: dict, moralis_api_key: str):
        """Collect Web3 EVM wallet data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary
            moralis_api_key: Moralis API key for Web3 data

        """
        wallet_address = self.config.get_account_env_value(account_config, "wallet_address_env")
        chains = account_config.get("chains", [])

        if not wallet_address:
            self.logger.info(f"Skipping {account_name} - no wallet address configured")
            return

        if not moralis_api_key:
            self.logger.info(f"Skipping {account_name} - no Moralis API key configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} wallet data")
            repository = Web3Repository(self._get_legacy_config(), moralis_api_key)

            for chain in chains:
                chain_name = f"{account_name} {chain.upper()}"
                repository.get_and_store_evm_wallet(chain_name, wallet_address, chain)

            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")

    def _collect_web3_solana_account(self, account_name: str, account_config: dict, moralis_api_key: str):
        """Collect Web3 Solana wallet data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary
            moralis_api_key: Moralis API key for Web3 data

        """
        wallet_address = self.config.get_account_env_value(account_config, "wallet_address_env")
        network = account_config.get("network", "mainnet")

        if not wallet_address:
            self.logger.info(f"Skipping {account_name} - no wallet address configured")
            return

        if not moralis_api_key:
            self.logger.info(f"Skipping {account_name} - no Moralis API key configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} wallet data")
            repository = Web3Repository(self._get_legacy_config(), moralis_api_key)
            repository.get_and_store_sol_wallet(account_name, wallet_address, network)
            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")

    def _collect_cosmos_account(self, account_name: str, account_config: dict):
        """Collect Cosmos-based wallet data.

        Args:
            account_name: Name of the account
            account_config: Account configuration dictionary

        """
        wallet_address = self.config.get_account_env_value(account_config, "wallet_address_env")
        network = account_config.get("network", "osmosis")

        if not wallet_address:
            self.logger.info(f"Skipping {account_name} - no wallet address configured")
            return

        try:
            self.logger.info(f"Collecting {account_name} wallet data")
            repository = CosmosRepository(self._get_legacy_config())

            if network.lower() == "osmosis":
                repository.get_and_store_wallet(account_name, wallet_address)
                repository.get_and_store_pools(account_name, wallet_address)
            else:
                self.logger.warning(f"Unsupported Cosmos network: {network}")
                return

            self.logger.info(f"{account_name} data collection completed")
        except Exception:
            self.logger.exception(f"{account_name} data collection failed")
