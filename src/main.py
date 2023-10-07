import os

from currency_converter import CurrencyConverter
from dotenv import load_dotenv

from src.connector.connector import BigQueryConnector

from src.repository.bank import BunqRepository
from src.repository.stock import DeGiroRepository
from src.repository.crypto import Web3Repository, CoinbaseRepository
from src.repository.crypto import CosmosRepository

load_dotenv()


class Main:
    def __init__(self):
        self.config = {
            "connector": BigQueryConnector(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                os.getenv("PROJECT_ID"),
                os.getenv("SCHEMA_ID")
            ),
            "converter": CurrencyConverter(
                ref_currency=os.getenv("PREFERRED_CURRENCY")
            ),
            "coinmarketcap_api_key": os.getenv("COINMARKETCAP_API_KEY")
        }

    def run(self):
        self.bunq()
        self.degiro()
        self.web3()
        self.cosmos()
        self.coinbase()

    def bunq(self):
        br = BunqRepository(
            self.config,
            os.getenv("BUNQ_API_KEY"),
            os.getenv("BUNQ_CONFIGURATION_FILE_PROD")
        )
        br.get_and_store_accounts("Bunq")

    def degiro(self):
        repo = DeGiroRepository(
            self.config,
            os.getenv("DEGIRO_USERNAME"),
            os.getenv("DEGIRO_PASSWORD"),
            os.getenv("DEGIRO_INT_ACCOUNT"),
            os.getenv("DEGIRO_TOTP")
        )
        repo.get_and_store_stocks("DeGiro")
        repo.get_and_store_account("Flatex")
        repo.logout()

    def web3(self):
        repo = Web3Repository(self.config, os.getenv("MORALIS_API_KEY"))
        repo.get_and_store_wallet("Metamask", os.getenv("METAMASK_WALLET_ADDRESS"), "eth")
        repo.get_and_store_wallet("Metamask", os.getenv("METAMASK_WALLET_ADDRESS"), "polygon")

    def cosmos(self):
        repo = CosmosRepository(self.config)
        repo.get_and_store_wallet("Keplr", os.getenv("OSMOSIS_WALLET_ADDRESS"))
        repo.get_and_store_pools("Keplr", os.getenv("OSMOSIS_WALLET_ADDRESS"))

    def coinbase(self):
        repo = CoinbaseRepository(self.config, os.getenv("COINBASE_API_KEY"), os.getenv("COINBASE_API_SECRET"))
        repo.get_and_store_wallet("Coinbase")


if __name__ == '__main__':
    Main().run()
