import os

from currency_converter import CurrencyConverter
from dotenv import load_dotenv

from src.connector.bigquery import BigQueryConnector
from src.logger.telegram import TelegramLogger

from src.repository.bank.bunq_repository import BunqRepository
from src.repository.stock.degiro_repository import DeGiroRepository
from src.repository.crypto.web3_repository import Web3Repository
from src.repository.crypto.coinbase_repository import CoinbaseRepository
from src.repository.crypto.cosmos_repository import CosmosRepository

from multiprocessing import Process

load_dotenv()


class Main:
    def __init__(self):
        self.config = {
            "connector": BigQueryConnector(
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
                os.getenv("PROJECT_ID"),
                os.getenv("SCHEMA_ID"),
                os.getenv("LOCATION")
            ),
            "converter": CurrencyConverter(
                ref_currency=os.getenv("PREFERRED_CURRENCY")
            ),
            "logger": TelegramLogger(
                "app.log",
                os.getenv("TELEGRAM_BOT_TOKEN"),
                os.getenv("TELEGRAM_CHAT_ID")
            ),
            "coinmarketcap_api_key": os.getenv("COINMARKETCAP_API_KEY")
        }

    def run(self):
        functions = [
            self.bunq,
            self.degiro,
            self.web3,
            self.cosmos,
            self.coinbase
        ]

        processes = []
        for function in functions:
            process = Process(target=function)
            process.start()
            processes.append(process)

        for process in processes:
            process.join()

        self.config["connector"].calculate_and_store_totals(
            os.getenv("BQ_ACCOUNT_NAME"),
            os.getenv("BQ_STOCK_NAME"),
            os.getenv("BQ_CRYPTO_NAME")
        )

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
        repo.get_and_store_evm_wallet(
            "Metamask Ethereum",
            os.getenv("METAMASK_WALLET_ADDRESS"),
            "eth"
        )
        repo.get_and_store_evm_wallet(
            "Metamask Polygon",
            os.getenv("METAMASK_WALLET_ADDRESS"),
            "polygon"
        )
        repo.get_and_store_evm_wallet(
            "Coinbase Wallet",
            os.getenv("COINBASE_WALLET_ADDRESS"),
            "eth"
        )
        repo.get_and_store_sol_wallet(
            "Helium Wallet",
            os.getenv("HELIUM_WALLET_ADDRESS"),
            "mainnet"
        )

    def cosmos(self):
        repo = CosmosRepository(self.config)
        repo.get_and_store_wallet("Keplr Wallet", os.getenv("OSMOSIS_WALLET_ADDRESS"))
        repo.get_and_store_pools("Osmosis Pools", os.getenv("OSMOSIS_WALLET_ADDRESS"))

    def coinbase(self):
        repo = CoinbaseRepository(self.config, os.getenv("COINBASE_API_KEY"), os.getenv("COINBASE_API_SECRET"))
        repo.get_and_store_wallets("Coinbase")


if __name__ == '__main__':
    Main().run()
