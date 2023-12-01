import pandas as pd

from coinbase.wallet.client import Client

from src.model.crypto import Crypto


class Coinbase(Crypto):
    def __init__(self, coinmarketcap_api_key: str, coinbase_api_key: str, coinbase_api_secret: str):
        super().__init__(coinmarketcap_api_key)
        self.client = Client(coinbase_api_key, coinbase_api_secret)

    def retrieve_wallet(self, currency: str):
        accounts = self.client.get_accounts()['data']
        rows = []

        for account in accounts:
            amount = float(account['balance']['amount'])
            symbol = account['balance']['currency']
            metadata = self.get_crypto_currency_metadata(symbol, currency)

            if metadata is not None:
                price = float(metadata.get('price', 0))
                if price is None:
                    price = 0
                portfolio_value = amount * price

                if portfolio_value > 1:
                    rows.append({
                        "name": metadata['name'],
                        "type": "Balance",
                        "symbol": symbol,
                        "amount": amount,
                        "current_value": price,
                        "portfolio_value": round(portfolio_value, 2),
                        "currency": currency
                    })

        return pd.DataFrame(rows)
