from datetime import datetime

from src.connector.connector import Connector
from src.model.bank import Bunq


class BunqRepository:
    def __init__(self, api_key, configuration_file, connector: Connector):
        self.bunq = Bunq(api_key, configuration_file)
        self.connector = connector

    def get_and_store_accounts(self):
        df = self.bunq.retrieve_accounts()
        df['date'] = datetime.now().date()

        metadata = {
            "schema_id": "bank",
            "table_id": "bunq"
        }

        self.connector.store_data(df, metadata)
