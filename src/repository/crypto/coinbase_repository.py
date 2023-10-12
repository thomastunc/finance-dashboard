import time
from datetime import datetime

from src.repository import Repository
from src.model.crypto.coinbase import Coinbase


class CoinbaseRepository(Repository):
    def __init__(self, config: dict, coinbase_api_key: str, coinbase_api_secret: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.coinbase = Coinbase(config["coinmarketcap_api_key"], coinbase_api_key, coinbase_api_secret)
        except Exception as e:
            self.logger.error(f"Error while initializing Coinbase: {e}")

    def get_and_store_wallets(self, source: str):
        for i in range(self.ATTEMPTS):
            try:
                df = self.coinbase.retrieve_wallet()
                df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

                df.insert(0, "source", source)
                df.insert(0, "date", datetime.now().date())

                self.connector.store_data(df, self.CRYPTO)
                self.logger.info(f"[{source}] Wallets retrieved and stored")
                break
            except Exception as e:
                self.logger.error(f"[{source}] Error while retrieving and storing wallets: {e}")
                if i == self.ATTEMPTS - 1:
                    self.connector.store_data_of_yesterday(self.BANK, source)
                else:
                    time.sleep(self.DELAY)
