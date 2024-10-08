import requests
import time

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
                time.sleep(3)
                return {
                    "name": data['data'][symbol]['name'],
                    "price": data['data'][symbol]['quote'][currency]['price']
                }
            else:
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
