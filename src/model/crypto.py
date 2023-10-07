import json
import math

import pandas as pd
import requests
from urllib.parse import quote

from moralis import evm_api

COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com"


class Crypto:
    def __init__(self, coinmarketcap_api_key: str):
        self.coinmarketcap_api_key = coinmarketcap_api_key
        self.base_url = COINMARKETCAP_BASE_URL

    def get_crypto_price(self, symbol: str, currency: str):
        params = {'symbol': symbol, 'convert': currency}
        headers = {'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key}

        try:
            endpoint = '/v1/cryptocurrency/quotes/latest'
            response = requests.get(self.base_url + endpoint, params=params, headers=headers)
            data = response.json()

            if 'data' in data and symbol in data['data']:
                return data['data'][symbol]['quote'][currency]['price']
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None


class Web3(Crypto):
    def __init__(self, coinmarketcap_api_key: str, web3_api_key: str):
        super().__init__(coinmarketcap_api_key)
        self.web3_api_key = web3_api_key

    def get_balance_from_address(self, params):
        balances = evm_api.token.get_wallet_token_balances(
            api_key=self.web3_api_key,
            params=params,
        )

        # TODO: fix this
        return None


class Cosmos(Crypto):
    def __init__(self, coinmarketcap_api_key: str, api_url: str, lcd_url: str, rpc_url: str):
        super().__init__(coinmarketcap_api_key)
        self.api_url = api_url
        self.lcd_url = lcd_url
        self.rpc_url = rpc_url

    def retrieve_wallet(self, address, currency: str = 'EUR'):
        balances = self.get_balances_from_address(address)
        rows = []

        for balance in balances:
            metadata = self.get_coin_metadata(denom=balance['denom'])
            amount = balance['amount']

            if metadata:
                current_value = self.get_crypto_price(metadata['symbol'], currency)
                exponent = metadata.get('exponent', 0)
                amount = float(amount) / math.pow(10, exponent)
                portfolio_value = amount * current_value

                if portfolio_value > 1:
                    rows.append({
                        "name": metadata['name'],
                        "symbol": metadata['symbol'],
                        "amount": amount,
                        "current_value": current_value,
                        "portfolio_value": portfolio_value,
                        "currency": currency
                    })

        return pd.DataFrame(rows)

    def retrieve_pools(self, address):
        balances = self.get_balances_from_pool()
        print(balances)
        return None

    def get_balances_from_address(self, address):
        responses = []

        endpoint = '/cosmos/bank/v1beta1/balances/'
        results = json.loads(requests.get(self.lcd_url + endpoint + address, timeout=60).content)
        responses += results['balances']
        pagination = results['pagination']['next_key']

        while pagination is not None:
            results = json.loads(
                requests.get(
                    self.lcd_url + endpoint + '?pagination.key=' + quote(str(pagination)),
                    timeout=60).content)
            responses += results['balances']
            pagination = results['pagination']['next_key']

        return responses

    def get_balances_from_pool(self):
        endpoint = '/cosmos/distribution/v1beta1/community_pool'
        return json.loads(requests.get(self.lcd_url + endpoint, timeout=60).content)

    def get_coin_metadata(self, symbol=None, denom=None):
        if denom:
            endpoint = '/search/v1/symbol?denom='
            response = json.loads(requests.get(self.api_url + endpoint + denom, timeout=60).content)
            symbol = response.get("symbol", None)
        if symbol:
            endpoint = f'/tokens/v2/{symbol}'
            return json.loads(requests.get(self.api_url + endpoint, timeout=60).content)[0]
        return None
