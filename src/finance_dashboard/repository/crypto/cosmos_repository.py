from datetime import datetime

from finance_dashboard.model.crypto.cosmos import Cosmos
from finance_dashboard.repository import Repository

OSMOSIS_ZONE_API_URL = "https://api-osmosis.imperator.co"
OSMOSIS_ZONE_LCD_URL = "https://lcd.osmosis.zone"
OSMOSIS_ZONE_RPC_URL = "https://rpc.osmosis.zone"


class CosmosRepository(Repository):
    """Repository for Cosmos ecosystem cryptocurrency data operations."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)
        self.cosmos = Cosmos(
            config["coinmarketcap_api_key"],
            OSMOSIS_ZONE_API_URL,
            OSMOSIS_ZONE_LCD_URL,
            OSMOSIS_ZONE_RPC_URL,
        )

    def get_and_store_wallet(self, source: str, address: str):
        """Retrieve and store Cosmos wallet data."""
        try:
            self.logger.debug(f"[{source}] Starting Cosmos wallet retrieval - Address: {address}")
            df = self.cosmos.retrieve_wallet(address, self.converter.ref_currency)

            # Enhanced debug logging for Cosmos wallet data
            if not df.empty:
                self.logger.debug(f"[{source}] Retrieved {len(df)} Cosmos assets:")
                for _, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}]   {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']}"
                    )

            # Convert currencies and log after conversion
            self.logger.debug(f"[{source}] Converting currencies for Cosmos wallet data")
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
            self.logger.info(f"[{source}] Wallet retrieved and stored")
        except Exception:
            self.logger.exception(f"[{source}] Error while retrieving and storing wallet")
            self.logger.warning(f"[{source}] Failed to retrieve new wallet data, no data will be stored")

    def get_and_store_pools(self, source: str, address: str):
        """Retrieve and store Osmosis pool data."""
        try:
            self.logger.debug(f"[{source}] Starting Osmosis pools retrieval - Address: {address}")
            df = self.cosmos.retrieve_osmosis_pools(address, self.converter.ref_currency)

            # Enhanced debug logging for Osmosis pool data
            if not df.empty:
                self.logger.debug(f"[{source}] Retrieved {len(df)} Osmosis pools:")
                for _, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}]   {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | "
                        f"Current Value: {row['current_value']} {row['currency']} | "
                        f"Portfolio Value: {row['portfolio_value']} {row['currency']}"
                    )

            # Convert currencies and log after conversion
            self.logger.debug(f"[{source}] Converting currencies for Osmosis pool data")
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
            self.logger.info(f"[{source}] Pools retrieved and stored")
        except Exception:
            self.logger.exception(f"[{source}] Error while retrieving and storing pools")
            self.logger.warning(f"[{source}] Failed to retrieve new pool data, no data will be stored")
