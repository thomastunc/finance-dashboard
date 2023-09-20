import os
from datetime import datetime
from dotenv import load_dotenv

import pandas_gbq
from google.oauth2 import service_account

from source.bank.bunq_api import Bunq
from source.stock.degiro_api import DeGiro

load_dotenv()

credentials = service_account.Credentials.from_service_account_file('config/service_account.json')
project_id = os.getenv("PROJECT_ID")

today = datetime.now().date()


def store_data_in_bigquery(df, schema_id, table_id):
    pandas_gbq.to_gbq(
        df,
        destination_table=f"{project_id}.{schema_id}.{table_id}",
        if_exists='append',
        project_id=project_id,
        credentials=credentials,
        table_schema=[{'name': 'date', 'type': 'DATE'}],
        progress_bar=False
    )


def bunq_etl():
    bunq = Bunq(
        os.getenv('BUNQ_API_KEY'),
        os.getenv('BUNQ_CONFIGURATION_FILE_PROD')
    )
    accounts = bunq.retrieve_accounts()
    accounts['date'] = today
    store_data_in_bigquery(accounts, "bank", "bunq")


def degiro_etl():
    degiro = DeGiro(
        os.getenv("DEGIRO_USERNAME"),
        os.getenv("DEGIRO_PASSWORD"),
        os.getenv("DEGIRO_INT_ACCOUNT"),
        os.getenv("DEGIRO_TOTP")
    )
    stocks = degiro.retrieve_stocks()
    degiro.logout()

    stocks['date'] = today
    store_data_in_bigquery(stocks, "stock", "degiro")


def main():
    bunq_etl()
    degiro_etl()


if __name__ == '__main__':
    main()
