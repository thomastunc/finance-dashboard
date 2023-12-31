from datetime import datetime, timedelta

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
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Get yesterday's data based on a SQL query
        query = f"""
        SELECT *
        FROM `{self.project_id}.{self.schema_id}.{table_name}`
        WHERE date = DATE('{yesterday}')
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

    def calculate_and_store_totals(self, account_name: str, stock_name: str, crypto_name: str):
        client = bigquery.Client(credentials=self.credentials, location=self.location)
        date = datetime.now().strftime('%Y-%m-%d')

        sql_statements = [
            f"""
            CREATE TABLE IF NOT EXISTS {self.schema_id}.total (
              date DATE,
              total_balance FLOAT64,
              source STRING
            )
            """,
            f"""
            INSERT INTO prd.total (date, total_balance, source)
            SELECT DATE, SUM(balance) AS total_balance, '{account_name}' AS source
            FROM {self.schema_id}.bank
            WHERE date = DATE('{date}')
            GROUP BY date
            """,
            f"""
            INSERT INTO prd.total (date, total_balance, source)
            SELECT DATE, SUM(portfolio_value) AS total_balance, '{stock_name}' AS source
            FROM {self.schema_id}.stock
            WHERE date = DATE('{date}')
            GROUP BY date
            """,
            f"""
            INSERT INTO prd.total (date, total_balance, source)
            SELECT DATE, SUM(portfolio_value) AS total_balance, '{crypto_name}' AS source
            FROM {self.schema_id}.crypto
            WHERE date = DATE('{date}')
            GROUP BY date
            """
        ]

        # Execute each SQL statement
        for sql in sql_statements:
            query_job = client.query(sql)
            query_job.result()
