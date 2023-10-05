from datetime import datetime

from src.connector.connector import Connector
from src.model.crypto import Web3, Cosmos


class Web3Repository:
    def __init__(self, coinmarketcap_api_key, web3_api_key, connector: Connector):
        self.web3 = Web3(coinmarketcap_api_key, web3_api_key)
        self.connector = connector

    def get_and_store_wallet_balance(self, address, chain):
        df = self.web3.get_balance_from_address({"address": address, "chain": chain})
        df['date'] = datetime.now().date()

        metadata = {
            "schema_id": "crypto",
            "table_id": "metamask"
        }
        self.connector.store_data(df, metadata)


class CosmosRepository:
    def __init__(self, coinmarketcap_api_key, connector):
        self.cosmos = Cosmos(
            coinmarketcap_api_key,
            api="https://api.osmosis.zone",
            lcd="https://lcd.osmosis.zone",
            rpc="https://rpc.osmosis.zone",
            denom='uosmo'
        )
        self.connector = connector

    def get_and_store_wallet_balance(self, address):
        df = self.cosmos.get_balances_from_address(address)
        df['date'] = datetime.now().date()

        metadata = {
            "schema_id": "crypto",
            "table_id": "metamask"
        }
        self.connector.store_data(df, metadata)

    def get_and_store_pool_balance(self, address):
        print(address)
        return None
