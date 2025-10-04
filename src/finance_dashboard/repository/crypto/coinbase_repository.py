from datetime import datetime

from finance_dashboard.model.crypto.coinbase import Coinbase
from finance_dashboard.repository import Repository


class CoinbaseRepository(Repository):
    """Repository for Coinbase cryptocurrency data operations."""

    def __init__(self, config: dict, coinbase_key_file: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.coinbase = Coinbase(config["coinmarketcap_api_key"], coinbase_key_file)
        except Exception:
            self.logger.exception("Error while initializing Coinbase")

    def get_and_store_wallets(self, source: str):
        """Retrieve and store Coinbase wallet data."""
        try:
            self.logger.debug(f"[{source}] Starting Coinbase wallet retrieval")
            df = self.coinbase.retrieve_wallet(self.converter.ref_currency)

            # Enhanced debug logging for Coinbase wallet data
            if not df.empty:
                self.logger.debug(f"[{source}] Retrieved {len(df)} Coinbase wallets:")
                for _, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}]   {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']}"
                    )

            # Convert currencies and log after conversion
            self.logger.debug(f"[{source}] Converting currencies for Coinbase wallet data")
            df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

            # Log after conversion
            if not df.empty:
                self.logger.debug(f"[{source}] After conversion:")
                for _, row in df.iterrows():
                    original_cv = row.get("original_current_value", "N/A")
                    original_portfolio_v = row.get("original_portfolio_value", "N/A")
                    original_currency = row.get("original_currency", "N/A")
                    self.logger.debug(
                        f"[{source}]   {row['name']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']} | "
                        f"Original: CV={original_cv}, PortV={original_portfolio_v} {original_currency}"
                    )

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.CRYPTO)
            self.logger.info(f"[{source}] Wallets retrieved and stored")
        except Exception:
            self.logger.exception("[{source}] Error while retrieving and storing wallets")
            self.logger.warning(f"[{source}] Failed to retrieve new wallet data, no data will be stored")
