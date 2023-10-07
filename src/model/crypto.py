import json
import math

import pandas as pd
import requests
from urllib.parse import quote

from moralis import evm_api

import coinbase
from coinbase.wallet.client import Client

COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com"


class Crypto:
    def __init__(self, coinmarketcap_api_key: str):
        self.coinmarketcap_api_key = coinmarketcap_api_key
        self.base_url = COINMARKETCAP_BASE_URL

    def get_crypto_currency_metadata(self, symbol: str, currency: str):
        params = {'symbol': symbol, 'convert': currency}
        headers = {'X-CMC_PRO_API_KEY': self.coinmarketcap_api_key}

        try:
            endpoint = '/v1/cryptocurrency/quotes/latest'
            response = requests.get(self.base_url + endpoint, params=params, headers=headers)
            data = response.json()

            if 'data' in data and symbol in data['data']:
                return {
                    "name": data['data'][symbol]['name'],
                    "price": data['data'][symbol]['quote'][currency]['price']
                }
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None


class Web3(Crypto):
    def __init__(self, coinmarketcap_api_key: str, web3_api_key: str):
        super().__init__(coinmarketcap_api_key)
        self.web3_api_key = web3_api_key

    def retrieve_wallet(self, params: dict, currency: str):
        balances = evm_api.token.get_wallet_token_balances(
            api_key=self.web3_api_key,
            params=params,
        )

        rows = []
        for balance in balances:
            if not balance['possible_spam']:
                metadata = self.get_crypto_currency_metadata(balance['symbol'], currency)
                name = metadata['name']
                current_value = metadata['price']
                amount = balance['balance']
                exponent = balance.get('decimals', 0)
                amount = float(amount) / math.pow(10, exponent)
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


class Cosmos(Crypto):
    def __init__(self, coinmarketcap_api_key: str, api_url: str, lcd_url: str, rpc_url: str):
        super().__init__(coinmarketcap_api_key)
        self.api_url = api_url
        self.lcd_url = lcd_url
        self.rpc_url = rpc_url

    def retrieve_wallet(self, address, currency):
        balances = self.get_balances_from_address(address)
        rows = []

        for balance in balances:
            metadata = self.get_coin_metadata(denom=balance['denom'])
            amount = balance['amount']

            if metadata:
                current_value = self.get_crypto_currency_metadata(metadata['symbol'], currency)['price']
                exponent = metadata.get('exponent', 0)
                amount = float(amount) / math.pow(10, exponent)
                portfolio_value = amount * current_value

                if portfolio_value > 1:
                    rows.append({
                        "name": metadata['name'],
                        "type": "Balance",
                        "symbol": metadata['symbol'],
                        "amount": amount,
                        "current_value": current_value,
                        "portfolio_value": round(portfolio_value, 2),
                        "currency": currency
                    })

        return pd.DataFrame(rows)

    def retrieve_osmosis_pools(self, address, currency):
        defis = self.get_balances_from_pool(address)
        rows = []

        for defi in defis:
            pool_id = defi['denom'].split('/')[-1]
            metadata = self.get_osmosis_pool_metadata(pool_id)
            amount = self.calculate_pool_amount(defi['denom'], defi['amount'])

            if metadata:
                current_value = self.get_crypto_currency_metadata(metadata['secondary_symbol'], currency)['price']
                exponent = metadata.get('exponent', 0)
                amount = float(amount) / math.pow(10, exponent)
                portfolio_value = amount * current_value

                if portfolio_value > 1:
                    rows.append({
                        "name": f"{metadata['primary_symbol']} / {metadata['secondary_symbol']} Pool",
                        "type": "DeFi",
                        "symbol": f"{metadata['primary_symbol']}/{metadata['secondary_symbol']}",
                        "amount": amount,
                        "current_value": current_value,
                        "portfolio_value": round(portfolio_value, 2),
                        "currency": currency
                    })

        return pd.DataFrame(rows)

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

    def get_balances_from_pool(self, address):
        endpoint = '/osmosis/superfluid/v1beta1/total_delegation_by_delegator/'
        results = json.loads(requests.get(self.lcd_url + endpoint + address, timeout=60).content)
        return results['total_delegated_coins']

    def get_coin_metadata(self, symbol=None, denom=None):
        if denom:
            endpoint = '/search/v1/symbol?denom='
            response = json.loads(requests.get(self.api_url + endpoint + denom, timeout=60).content)
            symbol = response.get("symbol", None)
        if symbol:
            endpoint = f'/tokens/v2/{symbol}'
            return json.loads(requests.get(self.api_url + endpoint, timeout=60).content)[0]
        return None

    def get_osmosis_pool_metadata(self, pool_id=None):
        if pool_id:
            endpoint = f'/pools/v2/{pool_id}'
            response = json.loads(requests.get(self.api_url + endpoint, timeout=60).content)

            metadata_primary_coin = response[0]
            metadata_secondary_coin = response[1]

            return {
                "primary_symbol": metadata_primary_coin['symbol'],
                "secondary_symbol": metadata_secondary_coin['symbol'],
                "exponent": 6
            }
        return None

    def calculate_pool_amount(self, denom: str, amount: str):
        endpoint = "/osmosis/superfluid/v1beta1/asset_multiplier?denom="
        response = json.loads(requests.get(self.lcd_url + endpoint + denom, timeout=60).content)
        multiplier = response['osmo_equivalent_multiplier']['multiplier']
        return float(amount) * float(multiplier) * 2


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
