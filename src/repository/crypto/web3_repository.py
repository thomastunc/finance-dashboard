from datetime import datetime

from src.repository import Repository
from src.model.crypto.web3 import Web3


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
