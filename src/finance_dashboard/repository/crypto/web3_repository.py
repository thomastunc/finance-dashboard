from datetime import datetime

from finance_dashboard.model.crypto.web3 import Web3
from finance_dashboard.repository import Repository


class Web3Repository(Repository):
    """Repository for Web3 blockchain (EVM/Solana) data operations."""

    def __init__(self, config: dict, web3_api_key: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)
        self.web3 = Web3(config["coinmarketcap_api_key"], web3_api_key)

    def get_and_store_evm_wallet(self, source: str, address: str, chain: str):
        """Retrieve and store EVM-compatible blockchain wallet data."""
        try:
            self.logger.debug(f"[{source}] Starting EVM wallet retrieval from {chain} - Address: {address}")
            df = self.web3.retrieve_evm_wallet(address, chain, self.converter.ref_currency)

            # Enhanced debug logging for EVM wallet data
            if not df.empty:
                self.logger.debug(f"[{source}] Retrieved {len(df)} EVM tokens:")
                for _, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}]   {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']}"
                    )

            # Convert currencies and log after conversion
            self.logger.debug(f"[{source}] Converting currencies for EVM wallet data")
            df = self.convert_currencies(df, ["current_value", "portfolio_value"])

            # Log after conversion
            if not df.empty:
                self.logger.debug(f"[{source}] After conversion:")
                for _, row in df.iterrows():
                    original_cv = row.get("original_current_value", "N/A")
                    original_pv = row.get("original_portfolio_value", "N/A")
                    original_currency = row.get("original_currency", "N/A")
                    self.logger.debug(
                        f"[{source}]   {row['name']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']} | "
                        f"Original: CV={original_cv}, PV={original_pv} {original_currency}"
                    )

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.CRYPTO)
            self.logger.info(f"[{source}] EVM wallet retrieved and stored")
        except Exception:
            self.logger.exception(f"[{source}] Error while retrieving and storing EVM wallet")
            self.logger.warning(f"[{source}] Failed to retrieve new EVM wallet data, no data will be stored")

    def get_and_store_sol_wallet(self, source: str, address: str, network: str):
        """Retrieve and store Solana wallet data."""
        try:
            self.logger.debug(f"[{source}] Starting Solana wallet retrieval from {network} - Address: {address}")
            df = self.web3.retrieve_sol_wallet(address, network, self.converter.ref_currency)

            # Enhanced debug logging for Solana wallet data
            if not df.empty:
                self.logger.debug(f"[{source}] Retrieved {len(df)} Solana tokens:")
                for _, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}]   {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']}"
                    )

            # Convert currencies and log after conversion
            self.logger.debug(f"[{source}] Converting currencies for Solana wallet data")
            df = self.convert_currencies(df, ["current_value", "portfolio_value"])

            # Log after conversion
            if not df.empty:
                self.logger.debug(f"[{source}] After conversion:")
                for _, row in df.iterrows():
                    original_cv = row.get("original_current_value", "N/A")
                    original_pv = row.get("original_portfolio_value", "N/A")
                    original_currency = row.get("original_currency", "N/A")
                    self.logger.debug(
                        f"[{source}]   {row['name']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']} | "
                        f"Original: CV={original_cv}, PV={original_pv} {original_currency}"
                    )

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.CRYPTO)
            self.logger.info(f"[{source}] Solana wallet retrieved and stored")
        except Exception:
            self.logger.exception(f"[{source}] Error while retrieving and storing Solana wallet")
            self.logger.warning(f"[{source}] Failed to retrieve new Solana wallet data, no data will be stored")
