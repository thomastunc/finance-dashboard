from datetime import datetime

from src.connector.connector import Connector
from src.model.stock import DeGiro


class DeGiroRepository:
    def __init__(self, username, password, int_account, totp, connector: Connector):
        self.degiro = DeGiro(username, password, int_account, totp)
        self.connector = connector

    def get_and_store_stocks(self):
        df = self.degiro.retrieve_stocks()
        df['date'] = datetime.now().date()

        metadata = {
            "schema_id": "stock",
            "table_id": "degiro"
        }

        self.connector.store_data(df, metadata)

    def get_and_store_account(self):
        df = self.degiro.retrieve_account()
        df['date'] = datetime.now().date()

        metadata = {
            "schema_id": "bank",
            "table_id": "flatex"
        }

        self.connector.store_data(df, metadata)

    def logout(self):
        self.degiro.logout()
