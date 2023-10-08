from datetime import datetime

from src.repository import Repository
from src.model.crypto.coinbase import Coinbase


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
