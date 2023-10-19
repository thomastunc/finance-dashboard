import time
from datetime import datetime

from src.repository import Repository
from src.model.crypto.web3 import Web3


class Web3Repository(Repository):
    def __init__(self, config: dict, web3_api_key: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)
        self.web3 = Web3(config["coinmarketcap_api_key"], web3_api_key)

    def get_and_store_evm_wallet(self, source: str, address: str, chain: str):
        for i in range(self.ATTEMPTS):
            try:
                df = self.web3.retrieve_evm_wallet(address, chain, self.converter.ref_currency)
                df = self.convert_currencies(df, ["current_value", "portfolio_value"])

                df.insert(0, "source", source)
                df.insert(0, "date", datetime.now().date())

                self.connector.store_data(df, self.CRYPTO)
                self.logger.info(f"[{source}] EVM wallet retrieved and stored")
                break
            except Exception as e:
                self.logger.error(f"[{source}] Error while retrieving and storing EVM wallet: {e}")
                if i == self.ATTEMPTS - 1:
                    self.connector.store_data_of_yesterday(self.CRYPTO, source)
                else:
                    time.sleep(self.DELAY)

    def get_and_store_sol_wallet(self, source: str, address: str, network: str):
        for i in range(self.ATTEMPTS):
            try:
                df = self.web3.retrieve_sol_wallet(address, network, self.converter.ref_currency)
                df = self.convert_currencies(df, ["current_value", "portfolio_value"])

                df.insert(0, "source", source)
                df.insert(0, "date", datetime.now().date())

                self.connector.store_data(df, self.CRYPTO)
                self.logger.info(f"[{source}] Solana wallet retrieved and stored")
                break
            except Exception as e:
                self.logger.error(f"[{source}] Error while retrieving and storing Solana wallet: {e}")
                if i == self.ATTEMPTS - 1:
                    self.connector.store_data_of_yesterday(self.CRYPTO, source)
                else:
                    time.sleep(self.DELAY)
