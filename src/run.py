import os
from dotenv import load_dotenv

from google.oauth2 import service_account

from src.connector.connector import BigQueryConnector

from src.repository.bank import BunqRepository
from src.repository.crypto import Web3Repository
from src.repository.stock import DeGiroRepository

load_dotenv()


def big_query():
    gcp_credentials = service_account.Credentials.from_service_account_file('config/service_account.json')
    project_id = os.getenv("PROJECT_ID")
    return BigQueryConnector(gcp_credentials, project_id)


def bunq(connector):
    with BunqRepository(
            os.getenv('BUNQ_API_KEY'),
            os.getenv('BUNQ_CONFIGURATION_FILE_PROD'),
            connector=connector
    ) as repo:
        repo.get_and_store_accounts()


def degiro(connector):
    with DeGiroRepository(
            os.getenv("DEGIRO_USERNAME"),
            os.getenv("DEGIRO_PASSWORD"),
            os.getenv("DEGIRO_INT_ACCOUNT"),
            os.getenv("DEGIRO_TOTP"),
            connector=connector
    ) as repo:
        repo.get_and_store_stocks()
        repo.get_and_store_account()


def web3(connector):
    with Web3Repository(
            os.getenv("MORALIS_API_KEY"),
            connector=connector
    ) as repo:
        repo.get_and_store_wallet_token_balances()


def main():
    bq_connector = big_query()

    bunq(connector=bq_connector)
    degiro(connector=bq_connector)

    # web3(connector=bq_connector)


if __name__ == '__main__':
    main()
