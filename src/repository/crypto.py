from datetime import datetime

from src.model.crypto import Web3, Cosmos
from src.repository import Repository

OSMOSIS_ZONE_API_URL = "https://api.osmosis.zone"
OSMOSIS_ZONE_LCD_URL = "https://lcd.osmosis.zone"
OSMOSIS_ZONE_RPC_URL = "https://rpc.osmosis.zone"


class Web3Repository(Repository):
    def __init__(self, config: dict, coinmarketcap_api_key: str, web3_api_key: str):
        super().__init__(config)
        self.web3 = Web3(coinmarketcap_api_key, web3_api_key)

    def get_and_store_wallet(self, source: str, address: str, chain: str):
        df = self.web3.get_balance_from_address({"address": address, "chain": chain})
        df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)


class CosmosRepository(Repository):
    def __init__(self, config: dict, coinmarketcap_api_key: str):
        super().__init__(config)
        self.cosmos = Cosmos(
            coinmarketcap_api_key,
            OSMOSIS_ZONE_API_URL,
            OSMOSIS_ZONE_LCD_URL,
            OSMOSIS_ZONE_RPC_URL
        )

    def get_and_store_wallet(self, source: str, address: str):
        df = self.cosmos.retrieve_wallet(address)
        df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)

    def get_and_store_pools(self, source: str, address: str):
        df = self.cosmos.retrieve_pools(address)
        df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)
