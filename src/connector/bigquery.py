from datetime import datetime

import pandas_gbq
from google.cloud import bigquery
from google.oauth2 import service_account
from pandas import DataFrame

from src import schema
from src.connector import Connector


class BigQueryConnector(Connector):
    def __init__(self, credentials_path: str, project_id: str, schema_id: str, location: str):
        self.credentials = service_account.Credentials.from_service_account_file(credentials_path)

        self.project_id = project_id
        self.schema_id = schema_id
        self.location = location

    def store_data(self, df: DataFrame, table_name: str):
        pandas_gbq.to_gbq(
            df,
            destination_table=f"{self.project_id}.{self.schema_id}.{table_name}",
            if_exists='append',
            project_id=self.project_id,
            credentials=self.credentials,
            table_schema=self.get_table_schema(table_name),
            progress_bar=False,
            location=self.location
        )

    def store_data_of_yesterday(self, table_name: str, source: str):
        client = bigquery.Client(credentials=self.credentials, location=self.location)

        # Get yesterday's data based on a SQL query
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.schema_id}.{table_name}`
        WHERE date = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        AND source = '{source}'
        """

        df = client.query(query).result().to_dataframe()
        df["date"] = datetime.now().date()

        self.store_data(df, table_name)

    @staticmethod
    def get_table_schema(table_name: str):
        if table_name == "bank":
            return schema.bank()
        elif table_name == "stock":
            return schema.stock()
        elif table_name == "crypto":
            return schema.crypto()
