import time
from datetime import datetime

from src.repository import Repository

from src.model.crypto.cosmos import Cosmos

OSMOSIS_ZONE_API_URL = "https://api-osmosis.imperator.co"
OSMOSIS_ZONE_LCD_URL = "https://lcd.osmosis.zone"
OSMOSIS_ZONE_RPC_URL = "https://rpc.osmosis.zone"


class CosmosRepository(Repository):
    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)
        self.cosmos = Cosmos(
            config["coinmarketcap_api_key"],
            OSMOSIS_ZONE_API_URL,
            OSMOSIS_ZONE_LCD_URL,
            OSMOSIS_ZONE_RPC_URL
        )

    def get_and_store_wallet(self, source: str, address: str):
        for i in range(self.ATTEMPTS):
            try:
                df = self.cosmos.retrieve_wallet(address, self.converter.ref_currency)
                df = self.convert_currencies(df, ["current_value", "portfolio_value"])

                df.insert(0, "source", source)
                df.insert(0, "date", datetime.now().date())

                self.connector.store_data(df, self.CRYPTO)
                self.logger.info(f"[{source}] Wallet retrieved and stored")
                break
            except Exception as e:
                self.logger.error(f"[{source}] Error while retrieving and storing wallet: {e}")
                if i == self.ATTEMPTS - 1:
                    self.connector.store_data_of_yesterday(self.CRYPTO, source)
                else:
                    time.sleep(self.DELAY)

    def get_and_store_pools(self, source: str, address: str):
        for i in range(self.ATTEMPTS):
            try:
                df = self.cosmos.retrieve_osmosis_pools(address, self.converter.ref_currency)
                df = self.convert_currencies(df, ["current_value", "portfolio_value"])

                df.insert(0, "source", source)
                df.insert(0, "date", datetime.now().date())

                self.connector.store_data(df, self.CRYPTO)
                self.logger.info(f"[{source}] Pools retrieved and stored")
                break
            except Exception as e:
                self.logger.error(f"[{source}] Error while retrieving and storing pools: {e}")
                if i == self.ATTEMPTS - 1:
                    self.connector.store_data_of_yesterday(self.CRYPTO, source)
                else:
                    time.sleep(self.DELAY)
