import pandas_gbq
from google.oauth2 import service_account

from src import schema


class Connector:
    def store_data(self, df, table_name):
        raise NotImplementedError


class BigQueryConnector(Connector):
    def __init__(self, credentials_path: str, project_id: str, schema_id: str):
        self.credentials = service_account.Credentials.from_service_account_file(credentials_path)
        self.project_id = project_id
        self.schema_id = schema_id

    def store_data(self, df, table_name: str):
        pandas_gbq.to_gbq(
            df,
            destination_table=f"{self.project_id}.{self.schema_id}.{table_name}",
            if_exists='append',
            project_id=self.project_id,
            credentials=self.credentials,
            table_schema=self.get_table_schema(table_name),
            progress_bar=False
        )

    @staticmethod
    def get_table_schema(table_name: str):
        if table_name == "bank":
            return schema.bank()
        elif table_name == "stock":
            return schema.stock()
        elif table_name == "crypto":
            return schema.crypto()
