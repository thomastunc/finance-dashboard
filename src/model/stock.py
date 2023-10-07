import pandas as pd

from degiro_connector.core.helpers import pb_handler
from degiro_connector.trading.api import API
from degiro_connector.trading.models.trading_pb2 import Credentials, Update, ProductSearch, ProductsInfo


class DeGiro:
    def __init__(self, username, password, int_account, totp):
        self.trading_api = API(credentials=Credentials(
            username=username,
            password=password,
            int_account=int(int_account),
            totp_secret_key=totp
        ))
        self.trading_api.connect()

    def search_stock(self, index_id):
        request = ProductsInfo.Request()
        request.products.extend([int(index_id)])

        products_info = self.trading_api.get_products_info(
            request=request,
            raw=True,
        )

        return products_info

    def retrieve_stocks(self):
        request_list = Update.RequestList()
        request_list.values.extend([Update.Request(option=Update.Option.PORTFOLIO, last_updated=0)])

        update = self.trading_api.get_update(request_list=request_list, raw=False)
        update_dict = pb_handler.message_to_dict(message=update)

        portfolio_df = pd.DataFrame(update_dict["portfolio"]["values"])
        portfolio_df = portfolio_df[portfolio_df['positionType'] == 'PRODUCT']
        portfolio_df = portfolio_df[portfolio_df['size'] > 0]

        rows = []

        for item in portfolio_df.index:
            product_id = portfolio_df['id'][item]
            stock_metadata = self.search_stock(product_id)

            currency = stock_metadata['data'][product_id]['currency']
            purchase_value = portfolio_df['breakEvenPrice'][item]
            current_value = portfolio_df['price'][item]
            portfolio_value = portfolio_df['value'][item]

            rows.append({
                "name": stock_metadata['data'][product_id]['name'],
                "symbol": stock_metadata['data'][product_id]['symbol'],
                "amount": int(portfolio_df['size'][item]),
                "purchase_value": purchase_value,
                "current_value": current_value,
                "portfolio_value": round(portfolio_value, 2),
                "currency": currency
            })

        return pd.DataFrame(rows)

    def retrieve_account(self):
        request_list = Update.RequestList()
        request_list.values.extend([Update.Request(option=Update.Option.TOTALPORTFOLIO, last_updated=0)])

        update = self.trading_api.get_update(request_list=request_list, raw=False)
        update_dict = pb_handler.message_to_dict(message=update)

        client_details_table = self.trading_api.get_client_details()

        rows = [{
            "name": "Flatex",
            "iban": client_details_table['data']['flatexBankAccount']['iban'],
            "balance": float(update_dict['total_portfolio']['values']['totalCash']),
            "currency": update_dict['total_portfolio']['values']['cashFundCompensationCurrency']
        }]

        return pd.DataFrame(rows)

    def logout(self):
        self.trading_api.logout()
