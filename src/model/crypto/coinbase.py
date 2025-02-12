import pandas as pd

from coinbase.rest import RESTClient

from src.model.crypto import Crypto


class Coinbase(Crypto):
    def __init__(self, coinmarketcap_api_key: str, coinbase_key_file: str):
        super().__init__(coinmarketcap_api_key)
        self.client = RESTClient(key_file=coinbase_key_file)

    def retrieve_wallet(self, currency: str):
        accounts = self.client.get_accounts(250)['accounts']
        rows = []

        for account in accounts:
            amount = float(account['available_balance']['value'])
            symbol = account['available_balance']['currency']
            metadata = self.get_crypto_currency_metadata(symbol, currency)

            if metadata is not None:
                price = float(metadata.get('price', 0))
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
