import math

import pandas as pd
from moralis import sol_api, evm_api

from src.model.crypto import Crypto


class Web3(Crypto):
    def __init__(self, coinmarketcap_api_key: str, web3_api_key: str):
        super().__init__(coinmarketcap_api_key)
        self.web3_api_key = web3_api_key

    def retrieve_sol_wallet(self, address: str, network: str, currency: str):
        balances = sol_api.account.get_portfolio(
            api_key=self.web3_api_key,
            params={
                "address": address,
                "network": network
            },
        )['tokens']

        rows = []
        for balance in balances:
            metadata = self.get_crypto_currency_metadata(balance['symbol'], currency)
            if metadata is not None:
                name = metadata['name']
                current_value = metadata.get('price', 0)
                if current_value is None:
                    current_value = 0
                amount = float(balance['amount'])
                portfolio_value = amount * current_value

                if portfolio_value > 1:
                    rows.append({
                        "name": name,
                        "type": "Balance",
                        "symbol": balance['symbol'],
                        "amount": amount,
                        "current_value": current_value,
                        "portfolio_value": round(portfolio_value, 2),
                        "currency": currency
                    })

        return pd.DataFrame(rows)

    def retrieve_evm_wallet(self, address: str, chain: str, currency: str):
        balances = evm_api.token.get_wallet_token_balances(
            api_key=self.web3_api_key,
            params={
                "address": address,
                "chain": chain
            }
        )

        rows = []
        for balance in balances:
            if not balance['possible_spam']:
                metadata = self.get_crypto_currency_metadata(balance['symbol'], currency)
                if metadata is not None:
                    name = metadata['name'] if metadata else balance['name']
                    current_value = metadata.get('price', 0)
                    if current_value is None:
                        current_value = 0
                    amount = balance['balance']
                    exponent = balance.get('decimals', 0)
                    amount = float(amount) / math.pow(10, exponent)
                    portfolio_value = amount * current_value

                    if portfolio_value > 1 or current_value == 0:
                        rows.append({
                            "name": name,
                            "type": "Balance",
                            "symbol": balance['symbol'],
                            "amount": amount,
                            "current_value": current_value,
                            "portfolio_value": round(portfolio_value, 2),
                            "currency": currency
                        })

        return pd.DataFrame(rows)
