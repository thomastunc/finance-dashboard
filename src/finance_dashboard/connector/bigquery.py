import contextlib
import logging
from datetime import datetime

import pandas_gbq
from google.cloud import bigquery
from google.oauth2 import service_account
from pandas import DataFrame

from finance_dashboard import schema
from finance_dashboard.connector import Connector


class BigQueryConnector(Connector):
    """BigQuery connector for storing and retrieving financial data."""

    def __init__(self, credentials_path: str, project_id: str, schema_id: str, location: str):
        self.credentials = service_account.Credentials.from_service_account_file(credentials_path)

        self.project_id = project_id
        self.schema_id = schema_id
        self.location = location
        self.logger = logging.getLogger(__name__)

    def store_data(self, df: DataFrame, table_name: str):
        """Upsert data into BigQuery table based on unique combination of date, source, and name.

        If a record with the same date, source, and name exists, it will be updated.
        Otherwise, a new record will be inserted.
        """
        if df.empty:
            return

        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        # Ensure the dataset exists before creating tables
        self._ensure_dataset_exists(client)

        # Check if the target table exists, create it if it doesn't
        self._ensure_table_exists(client, table_name)

        # First, upload the data to a temporary table
        temp_table_name = f"{table_name}_temp_{int(datetime.now().timestamp())}"
        temp_table_id = f"{self.project_id}.{self.schema_id}.{temp_table_name}"

        try:
            # Upload data to temporary table
            pandas_gbq.to_gbq(
                df,
                destination_table=temp_table_id,
                if_exists="replace",
                project_id=self.project_id,
                credentials=self.credentials,
                table_schema=self.get_table_schema(table_name),
                progress_bar=False,
                location=self.location,
            )

            # Perform upsert using MERGE statement
            merge_query = self._build_merge_query(table_name, temp_table_name)
            query_job = client.query(merge_query)
            query_job.result()  # Wait for the query to complete

        finally:
            # Clean up temporary table
            with contextlib.suppress(Exception):
                client.delete_table(temp_table_id)

    def _ensure_dataset_exists(self, client: bigquery.Client):
        """Check if the dataset exists, and create it if it doesn't."""
        dataset_id = f"{self.project_id}.{self.schema_id}"

        try:
            # Try to get the dataset - this will raise NotFound if it doesn't exist
            client.get_dataset(dataset_id)
        except Exception:
            # Dataset doesn't exist, create it
            self.logger.info(f"Dataset `{dataset_id}` does not exist, creating it now")
            dataset = bigquery.Dataset(dataset_id)
            dataset.location = self.location
            client.create_dataset(dataset, exists_ok=True)
            self.logger.info(f"Dataset `{dataset_id}` created successfully")

    def _ensure_table_exists(self, client: bigquery.Client, table_name: str):
        """Check if the table exists, and create it if it doesn't."""
        table_id = f"{self.project_id}.{self.schema_id}.{table_name}"

        try:
            # Try to get the table - this will raise NotFound if it doesn't exist
            client.get_table(table_id)
            # Table exists, no need to log
        except Exception:
            # Table doesn't exist, create it
            self._create_table(client, table_name)

    def _create_table(self, client: bigquery.Client, table_name: str):
        """Create a BigQuery table with the appropriate schema."""
        table_id = f"{self.project_id}.{self.schema_id}.{table_name}"
        schema_fields = self._get_bigquery_schema(table_name)

        self.logger.info(f"Table `{table_id}` does not exist, creating it now")
        table = bigquery.Table(table_id, schema=schema_fields)

        # Set table clustering for better performance
        if table_name in ["bank", "stock", "crypto"]:
            table.clustering_fields = ["date", "source"]

        client.create_table(table)
        self.logger.info(f"Table `{table_id}` created successfully")

    def _get_bigquery_schema(self, table_name: str):
        """Convert the schema dictionary to BigQuery schema fields."""
        schema_dict = self.get_table_schema(table_name)
        schema_fields = []

        for field in schema_dict:
            field_type = field["type"]
            field_mode = field.get("mode", "NULLABLE")

            # Convert pandas_gbq types to BigQuery types
            if field_type.upper() in ["STRING"]:
                bq_type = "STRING"
            elif field_type.upper() in ["FLOAT", "FLOAT64"]:
                bq_type = "FLOAT64"
            elif field_type.upper() in ["INTEGER", "INT64"]:
                bq_type = "INTEGER"
            elif field_type.upper() == "DATE":
                bq_type = "DATE"
            elif field_type.upper() == "DATETIME":
                bq_type = "DATETIME"
            elif field_type.upper() == "BOOLEAN":
                bq_type = "BOOLEAN"
            else:
                bq_type = "STRING"  # Default fallback

            schema_fields.append(bigquery.SchemaField(field["name"], bq_type, mode=field_mode))

        return schema_fields

    @staticmethod
    def get_table_schema(table_name: str):
        """Get schema definition for a given table name."""
        if table_name == "bank":
            return schema.bank()
        elif table_name == "stock":
            return schema.stock()
        elif table_name == "crypto":
            return schema.crypto()
        else:
            raise ValueError(f"Unknown table name: {table_name}")

    def dataset_exists(self) -> bool:
        """Check if the dataset exists."""
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)
        dataset_id = f"{self.project_id}.{self.schema_id}"
        try:
            client.get_dataset(dataset_id)
            return True
        except Exception:
            return False

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists."""
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)
        table_id = f"{self.project_id}.{self.schema_id}.{table_name}"
        try:
            client.get_table(table_id)
            return True
        except Exception:
            return False

    def view_exists(self, view_name: str) -> bool:
        """Check if a view exists."""
        return self.table_exists(view_name)  # Views are treated as tables in BigQuery API

    def setup_database(self, account_name: str, stock_name: str, crypto_name: str):
        """Set up the database schema (dataset, tables, and view) if they don't exist.

        This should be called once at startup to ensure the database structure is in place.
        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        self.logger.info("Starting database setup check")

        # 1. Ensure dataset exists
        if not self.dataset_exists():
            self._ensure_dataset_exists(client)
        else:
            self.logger.info(f"Dataset `{self.project_id}.{self.schema_id}` already exists")

        # 2. Ensure required tables exist
        # We need to create them before creating the view that references them
        self.logger.info("Checking required tables (bank, stock, crypto)")
        self.ensure_all_tables_exist()

        # 3. Ensure view exists
        if not self.view_exists("total"):
            self.logger.info("Creating totals view")
            self.create_totals_view(account_name, stock_name, crypto_name)
        else:
            self.logger.info(f"View `{self.project_id}.{self.schema_id}.total` already exists")

        self.logger.info("Database setup completed successfully")

    def create_totals_view(self, account_name: str, stock_name: str, crypto_name: str):
        """Create a regular view that automatically calculates totals from bank, stock, and crypto tables.

        This view will automatically reflect changes when the underlying tables are updated.
        Regular views don't have the same restrictions as materialized views.
        Only creates the view if it doesn't already exist.
        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        # Ensure the dataset exists before creating the view
        self._ensure_dataset_exists(client)

        # Check if view already exists
        if self.view_exists("total"):
            return  # View already exists, no need to recreate

        view_id = f"{self.project_id}.{self.schema_id}.total"
        self.logger.info(f"View `{view_id}` does not exist, creating it now")

        # Create the regular view that unions all totals
        # ruff: noqa: S608  # SQL injection is not a concern here as we control the values
        create_view_sql = f"""
        CREATE VIEW `{self.project_id}.{self.schema_id}.total`
        AS
        SELECT
            date,
            ROUND(SUM(balance), 2) AS total_balance,
            '{account_name}' AS source
        FROM `{self.project_id}.{self.schema_id}.bank`
        GROUP BY date

        UNION ALL

        SELECT
            date,
            ROUND(SUM(portfolio_value), 2) AS total_balance,
            '{stock_name}' AS source
        FROM `{self.project_id}.{self.schema_id}.stock`
        GROUP BY date

        UNION ALL

        SELECT
            date,
            ROUND(SUM(portfolio_value), 2) AS total_balance,
            '{crypto_name}' AS source
        FROM `{self.project_id}.{self.schema_id}.crypto`
        GROUP BY date
        """

        # Create the new view
        query_job = client.query(create_view_sql)
        query_job.result()
        self.logger.info(f"View `{view_id}` created successfully")

    def get_totals(self, start_date: str | None = None, end_date: str | None = None):
        """Query the totals view with optional date filtering.

        Args:
            start_date: Optional start date in 'YYYY-MM-DD' format
            end_date: Optional end date in 'YYYY-MM-DD' format

        Returns:
            DataFrame with the totals data

        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        where_clause = ""
        query_parameters = []

        if start_date and end_date:
            where_clause = "WHERE date BETWEEN @start_date AND @end_date"
            query_parameters.extend(
                [
                    bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                ]
            )
        elif start_date:
            where_clause = "WHERE date >= @start_date"
            query_parameters.append(bigquery.ScalarQueryParameter("start_date", "DATE", start_date))
        elif end_date:
            where_clause = "WHERE date <= @end_date"
            query_parameters.append(bigquery.ScalarQueryParameter("end_date", "DATE", end_date))

        # ruff: noqa: S608  # SQL injection is not a concern here as we control the values
        query = f"""
        SELECT
            date,
            source,
            total_balance
        FROM `{self.project_id}.{self.schema_id}.total`
        {where_clause}
        ORDER BY date DESC, source
        """

        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
        return client.query(query, job_config=job_config).to_dataframe()

    def _build_merge_query(self, table_name: str, temp_table_name: str) -> str:
        """Build a MERGE query for upsert operations based on the actual columns in the temp table.

        The unique key is the combination of date, source, and name.
        Only uses columns that exist in both target and source tables.
        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        # Get the actual columns from the temporary table
        temp_table_id = f"{self.project_id}.{self.schema_id}.{temp_table_name}"
        temp_table = client.get_table(temp_table_id)
        source_columns = [field.name for field in temp_table.schema]

        # Get target table schema columns
        target_schema = self.get_table_schema(table_name)
        target_columns = [field["name"] for field in target_schema]

        # Only use columns that exist in both source and target
        common_columns = [col for col in source_columns if col in target_columns]

        # Build column lists for the MERGE statement
        columns_list = ", ".join(common_columns)
        insert_values = ", ".join([f"source.{col}" for col in common_columns])

        # For the UPDATE part, exclude the unique key columns
        updateable_columns = [col for col in common_columns if col not in ["date", "source", "name"]]
        update_assignments = ", ".join([f"{col} = source.{col}" for col in updateable_columns])

        # ruff: noqa: S608  # SQL injection is not a concern here as we control the values
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

    def ensure_all_tables_exist(self):
        """Ensure all required tables (bank, stock, crypto) exist in the dataset.

        Creates them if they don't exist.
        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)
        required_tables = ["bank", "stock", "crypto"]

        for table_name in required_tables:
            table_id = f"{self.project_id}.{self.schema_id}.{table_name}"
            if self.table_exists(table_name):
                self.logger.info(f"Table `{table_id}` already exists")
            else:
                self._ensure_table_exists(client, table_name)

    def migrate_from_materialized_view(self):
        """Migrate from the old materialized view to the new regular view.

        This will drop the old materialized view if it exists.
        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        with contextlib.suppress(Exception):
            drop_materialized_view_sql = f"""
            DROP MATERIALIZED VIEW IF EXISTS `{self.project_id}.{self.schema_id}.total_materialized_view`
            """
            query_job = client.query(drop_materialized_view_sql)
            query_job.result()

    def get_daily_summary(self):
        """Get a summary of today's totals compared to yesterday's totals.

        Returns:
            dict with:
                - total_today: Total balance today across all categories
                - total_yesterday: Total balance yesterday
                - total_change: Change in total balance
                - total_change_pct: Percentage change in total balance
                - categories: List of dicts with per-category breakdown
                  - name: Category name (e.g., 'Bank', 'Stock', 'Crypto')
                  - today: Balance today
                  - yesterday: Balance yesterday
                  - change: Change in balance
                  - change_pct: Percentage change

        """
        client = bigquery.Client(credentials=self.credentials, project=self.project_id, location=self.location)

        # Query to get today's and yesterday's totals per category
        query = f"""
        WITH dates AS (
            SELECT
                MAX(date) AS today,
                DATE_SUB(MAX(date), INTERVAL 1 DAY) AS yesterday
            FROM `{self.project_id}.{self.schema_id}.total`
        ),
        today_data AS (
            SELECT
                source,
                SUM(total_balance) AS balance
            FROM `{self.project_id}.{self.schema_id}.total`
            WHERE date = (SELECT today FROM dates)
            GROUP BY source
        ),
        yesterday_data AS (
            SELECT
                source,
                SUM(total_balance) AS balance
            FROM `{self.project_id}.{self.schema_id}.total`
            WHERE date = (SELECT yesterday FROM dates)
            GROUP BY source
        )
        SELECT
            COALESCE(t.source, y.source) AS source,
            COALESCE(t.balance, 0) AS today_balance,
            COALESCE(y.balance, 0) AS yesterday_balance,
            COALESCE(t.balance, 0) - COALESCE(y.balance, 0) AS change,
            CASE
                WHEN COALESCE(y.balance, 0) > 0
                THEN ((COALESCE(t.balance, 0) - COALESCE(y.balance, 0)) / y.balance) * 100
                ELSE 0
            END AS change_pct
        FROM today_data t
        FULL OUTER JOIN yesterday_data y ON t.source = y.source
        ORDER BY source
        """

        df = client.query(query).to_dataframe()

        if df.empty:
            return None

        # Calculate totals
        total_today = float(df["today_balance"].sum())
        total_yesterday = float(df["yesterday_balance"].sum())
        total_change = float(df["change"].sum())
        total_change_pct = ((total_change / total_yesterday) * 100) if total_yesterday > 0 else 0

        # Build categories list
        categories = []
        for _, row in df.iterrows():
            categories.append(
                {
                    "name": row["source"],
                    "today": float(row["today_balance"]),
                    "yesterday": float(row["yesterday_balance"]),
                    "change": float(row["change"]),
                    "change_pct": float(row["change_pct"]),
                }
            )

        return {
            "total_today": total_today,
            "total_yesterday": total_yesterday,
            "total_change": total_change,
            "total_change_pct": total_change_pct,
            "categories": categories,
        }
