from datetime import datetime, timedelta

import pandas_gbq
from google.cloud import bigquery
from google.oauth2 import service_account
from pandas import DataFrame

from finance_dashboard import schema
from finance_dashboard.connector import Connector


class BigQueryConnector(Connector):
    def __init__(self, credentials_path: str, project_id: str, schema_id: str, location: str):
        self.credentials = service_account.Credentials.from_service_account_file(credentials_path)

        self.project_id = project_id
        self.schema_id = schema_id
        self.location = location

    def store_data(self, df: DataFrame, table_name: str):
        """
        Upsert data into BigQuery table based on unique combination of date, source, and name.
        If a record with the same date, source, and name exists, it will be updated.
        Otherwise, a new record will be inserted.
        """
        if df.empty:
            return
            
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)
        
        # First, upload the data to a temporary table
        temp_table_name = f"{table_name}_temp_{int(datetime.now().timestamp())}"
        temp_table_id = f"{self.project_id}.{self.schema_id}.{temp_table_name}"
        
        try:
            # Upload data to temporary table
            pandas_gbq.to_gbq(
                df,
                destination_table=temp_table_id,
                if_exists='replace',
                project_id=self.project_id,
                credentials=self.credentials,
                table_schema=self.get_table_schema(table_name),
                progress_bar=False,
                location=self.location
            )
            
            # Perform upsert using MERGE statement
            merge_query = self._build_merge_query(table_name, temp_table_name)
            query_job = client.query(merge_query)
            query_job.result()  # Wait for the query to complete
            
        finally:
            # Clean up temporary table
            try:
                client.delete_table(temp_table_id)
            except Exception:
                pass  # Ignore errors during cleanup

    @staticmethod
    def get_table_schema(table_name: str):
        if table_name == "bank":
            return schema.bank()
        elif table_name == "stock":
            return schema.stock()
        elif table_name == "crypto":
            return schema.crypto()
        else:
            raise ValueError(f"Unknown table name: {table_name}")

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
            MERGE `{self.project_id}.{self.schema_id}.total` AS target
            USING (
                SELECT DATE, SUM(balance) AS total_balance, '{account_name}' AS source
                FROM {self.schema_id}.bank
                WHERE date = DATE('{date}')
                GROUP BY date
            ) AS source
            ON target.date = source.date AND target.source = source.source
            WHEN MATCHED THEN
                UPDATE SET total_balance = source.total_balance
            WHEN NOT MATCHED THEN
                INSERT (date, total_balance, source)
                VALUES (source.date, source.total_balance, source.source)
            """,
            f"""
            MERGE `{self.project_id}.{self.schema_id}.total` AS target
            USING (
                SELECT DATE, SUM(portfolio_value) AS total_balance, '{stock_name}' AS source
                FROM {self.schema_id}.stock
                WHERE date = DATE('{date}')
                GROUP BY date
            ) AS source
            ON target.date = source.date AND target.source = source.source
            WHEN MATCHED THEN
                UPDATE SET total_balance = source.total_balance
            WHEN NOT MATCHED THEN
                INSERT (date, total_balance, source)
                VALUES (source.date, source.total_balance, source.source)
            """,
            f"""
            MERGE `{self.project_id}.{self.schema_id}.total` AS target
            USING (
                SELECT DATE, SUM(portfolio_value) AS total_balance, '{crypto_name}' AS source
                FROM {self.schema_id}.crypto
                WHERE date = DATE('{date}')
                GROUP BY date
            ) AS source
            ON target.date = source.date AND target.source = source.source
            WHEN MATCHED THEN
                UPDATE SET total_balance = source.total_balance
            WHEN NOT MATCHED THEN
                INSERT (date, total_balance, source)
                VALUES (source.date, source.total_balance, source.source)
            """
        ]

        # Execute each SQL statement
        for sql in sql_statements:
            query_job = client.query(sql)
            query_job.result()

    def _build_merge_query(self, table_name: str, temp_table_name: str) -> str:
        """
        Build a MERGE query for upsert operations based on the table schema.
        The unique key is the combination of date, source, and name.
        Assumes table schema is correct and up to date.
        """
        schema = self.get_table_schema(table_name)
        columns = [field['name'] for field in schema]
        
        # Build column lists for the MERGE statement
        columns_list = ', '.join(columns)
        insert_values = ', '.join([f"source.{col}" for col in columns])
        
        # For the UPDATE part, exclude the unique key columns
        updateable_columns = [col for col in columns if col not in ['date', 'source', 'name']]
        update_assignments = ', '.join([f"{col} = source.{col}" for col in updateable_columns])
        
        merge_query = f"""
        MERGE `{self.project_id}.{self.schema_id}.{table_name}` AS target
        USING `{self.project_id}.{self.schema_id}.{temp_table_name}` AS source
        ON target.date = source.date 
           AND target.source = source.source 
           AND target.name = source.name
        WHEN MATCHED THEN
          UPDATE SET {update_assignments}
        WHEN NOT MATCHED THEN
          INSERT ({columns_list})
          VALUES ({insert_values})
        """
        
        return merge_query
