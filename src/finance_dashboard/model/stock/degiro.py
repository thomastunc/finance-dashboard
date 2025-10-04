import pandas as pd

from degiro_connector.trading.api import API
from degiro_connector.trading.models.account import UpdateRequest, UpdateOption
from degiro_connector.trading.models.credentials import Credentials


class DeGiro:
    def __init__(self, username: str, password: str, int_account: str, totp: str):
        self.trading_api = API(credentials=Credentials(
            username=username,
            password=password,
            int_account=int(int_account),
            totp_secret_key=totp
        ))
        self.trading_api.connect()

    def search_stock(self, product_id: str):
        products_info = self.trading_api.get_products_info(
            product_list=[product_id],
            raw=True,
        )
        return products_info

    def retrieve_stocks(self):
        update = self.trading_api.get_update(
            request_list=[
                UpdateRequest(
                    option=UpdateOption.PORTFOLIO,
                    last_updated=0,
                ),
            ],
            raw=True
        )

        portfolio_df = pd.DataFrame(update["portfolio"]["value"])
        rows = []

        for item in portfolio_df.index:
            item_metadata = {entry['name']: entry.get('value', None) for entry in portfolio_df["value"][item]}
            item_amount = int(item_metadata['size'])

            if item_metadata['positionType'] == 'PRODUCT' and item_amount > 0:
                product_id = portfolio_df['id'][item]
                stock_metadata = self.search_stock(product_id)

                currency = stock_metadata['data'][product_id]['currency']
                purchase_value = item_metadata['breakEvenPrice']
                current_value = item_metadata['price']
                portfolio_value = item_metadata['value']

                rows.append({
                    "name": stock_metadata['data'][product_id]['name'],
                    "symbol": stock_metadata['data'][product_id]['symbol'],
                    "amount": item_amount,
                    "purchase_value": purchase_value,
                    "current_value": current_value,
                    "portfolio_value": round(portfolio_value, 2),
                    "currency": currency
                })

        return pd.DataFrame(rows)

    def retrieve_account(self):
        update = self.trading_api.get_update(
            request_list=[
                UpdateRequest(
                    option=UpdateOption.TOTAL_PORTFOLIO,
                    last_updated=0,
                ),
            ],
            raw=True
        )

        client_details_table = self.trading_api.get_client_details()
        total_portfolio_df = pd.DataFrame(update["totalPortfolio"])
        total_portfolio_metadata = {entry['name']: entry.get('value', None) for entry in total_portfolio_df["value"]}

        rows = [{
            "name": "Flatex",
            "iban": client_details_table['data']['flatexBankAccount']['iban'],
            "balance": total_portfolio_metadata["totalCash"],
            "currency": total_portfolio_metadata["cashFundCompensationCurrency"]
        }]

        return pd.DataFrame(rows)

    def logout(self):
        self.trading_api.logout()
