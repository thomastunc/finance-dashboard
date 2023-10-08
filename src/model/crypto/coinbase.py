import pandas as pd

from coinbase.wallet.client import Client

from src.model.crypto import Crypto


class Coinbase(Crypto):
    def __init__(self, coinmarketcap_api_key: str, coinbase_api_key: str, coinbase_api_secret: str):
        super().__init__(coinmarketcap_api_key)
        self.client = Client(coinbase_api_key, coinbase_api_secret)

    def retrieve_wallet(self):
        accounts = self.client.get_accounts()['data']
        rows = []

        for account in accounts:
            portfolio_value = float(account['native_balance']['amount'])
            currency = account['native_balance']['currency']

            if portfolio_value > 1:
                amount = float(account['balance']['amount'])
                symbol = account['currency']
                metadata = self.get_crypto_currency_metadata(symbol, currency)

                rows.append({
                    "name": metadata['name'],
                    "type": "Balance",
                    "symbol": symbol,
                    "amount": amount,
                    "current_value": metadata['price'],
                    "portfolio_value": round(portfolio_value, 2),
                    "currency": currency
                })

        return pd.DataFrame(rows)
