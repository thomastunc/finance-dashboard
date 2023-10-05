import json
import math

import requests
from urllib.parse import quote

from moralis import evm_api


class Crypto:
    def __init__(self, coinmarketcap_api_key):
        self.coinmarketcap_api_key = coinmarketcap_api_key
        self.base_url = 'https://pro-api.coinmarketcap.com'

    def get_crypto_price(self, symbol, currency='EUR'):
        params = {
            'symbol': symbol,
            'convert': currency,
        }
        headers = {
            'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key,
        }

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
    def __init__(self, coinmarketcap_api_key, web3_api_key):
        super().__init__(coinmarketcap_api_key)
        self.web3_api_key = web3_api_key

    def get_balance_from_address(self, params):
        return evm_api.token.get_wallet_token_balances(
            api_key=self.api_key,
            params=params,
        )


class Cosmos(Crypto):
    def __init__(self, coinmarketcap_api_key, api, lcd, rpc, denom):
        super().__init__(coinmarketcap_api_key)
        self.api = api
        self.lcd = lcd
        self.rpc = rpc
        self.denom = denom

    def get_balances_from_address(self, address):
        responses = []
        endpoint = '/cosmos/bank/v1beta1/balances/'
        try:
            results = json.loads(requests.get(self.lcd + endpoint + address, timeout=60).content)
            responses += results['balances']
            pagination = results['pagination']['next_key']
            while pagination is not None:
                results = json.loads(
                    requests.get(self.lcd + endpoint + '?pagination.key=' + quote(str(pagination)), timeout=60).content)
                responses += results['balances']
                pagination = results['pagination']['next_key']
            return responses
        except Exception:
            raise Exception

    def retrieve_crypto(self, address):
        balances = self.get_balances_from_address(address)
        rows = []

        for balance in balances:
            symbol = self.get_symbol_by_denom(balance['denom'])
            amount = balance['amount']

            if symbol:
                price = self.get_crypto_price(symbol)
                exponent = self.get_exponent(symbol)
                amount = float(amount) / math.pow(10, exponent)
                total_value = amount * price

                rows.append({
                    "symbol": symbol,
                    "amount": amount,
                    "price": price,
                    "total_value": total_value
                })

    def get_symbol_by_denom(self, denom):
        denom = self.denom if denom is None else denom
        endpoint = '/search/v1/symbol?denom='
        try:
            response = json.loads(requests.get(self.api + endpoint + denom, timeout=60).content)['symbol']
            return response if response != '' else None
        except Exception:
            raise Exception

    def get_exponent(self, symbol):
        endpoint = f'/tokens/v2/{symbol}'
        try:
            response = json.loads(requests.get(self.api + endpoint, timeout=60).content)[0]
            return response.get("exponent", 0)
        except Exception:
            raise Exception
