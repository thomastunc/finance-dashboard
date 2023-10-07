from datetime import datetime

from src.model.crypto import Web3, Cosmos, Coinbase
from src.repository import Repository

OSMOSIS_ZONE_API_URL = "https://api.osmosis.zone"
OSMOSIS_ZONE_LCD_URL = "https://lcd.osmosis.zone"
OSMOSIS_ZONE_RPC_URL = "https://rpc.osmosis.zone"


class Web3Repository(Repository):
    def __init__(self, config: dict, web3_api_key: str):
        super().__init__(config)
        self.web3 = Web3(config["coinmarketcap_api_key"], web3_api_key)

    def get_and_store_wallet(self, source: str, api_type: str, params: dict):
        if api_type == "evm":
            df = self.web3.retrieve_evm_wallet(params, self.converter.ref_currency)
        elif api_type == "sol":
            df = self.web3.retrieve_sol_wallet(params, self.converter.ref_currency)
        else:
            raise AttributeError("No valid type provided")

        df = self.convert_currencies(df, ["current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)


class CosmosRepository(Repository):
    def __init__(self, config: dict):
        super().__init__(config)
        self.cosmos = Cosmos(
            config["coinmarketcap_api_key"],
            OSMOSIS_ZONE_API_URL,
            OSMOSIS_ZONE_LCD_URL,
            OSMOSIS_ZONE_RPC_URL
        )

    def get_and_store_wallet(self, source: str, address: str):
        df = self.cosmos.retrieve_wallet(address, self.converter.ref_currency)
        df = self.convert_currencies(df, ["current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)

    def get_and_store_pools(self, source: str, address: str):
        df = self.cosmos.retrieve_osmosis_pools(address, self.converter.ref_currency)
        df = self.convert_currencies(df, ["current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)


class CoinbaseRepository(Repository):
    def __init__(self, config: dict, coinbase_api_key: str, coinbase_api_secret: str):
        super().__init__(config)
        self.coinbase = Coinbase(config["coinmarketcap_api_key"], coinbase_api_key, coinbase_api_secret)

    def get_and_store_wallet(self, source: str):
        df = self.coinbase.retrieve_wallet()
        df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.CRYPTO)
