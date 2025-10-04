import time

import requests

COINMARKETCAP_BASE_URL = "https://pro-api.coinmarketcap.com"


class Crypto:
    """Base class for cryptocurrency data retrieval and processing."""

    def __init__(self, coinmarketcap_api_key: str):
        self.coinmarketcap_api_key = coinmarketcap_api_key
        self.base_url = COINMARKETCAP_BASE_URL

    def get_crypto_currency_metadata(self, symbol: str, currency: str):
        """Get cryptocurrency metadata including price from CoinMarketCap API."""
        params = {"symbol": symbol, "convert": currency}
        headers = {"X-CMC_PRO_API_KEY": self.coinmarketcap_api_key}

        try:
            endpoint = "/v1/cryptocurrency/quotes/latest"
            time.sleep(3)
            response = requests.get(self.base_url + endpoint, params=params, headers=headers, timeout=30)
            data = response.json()

            if "data" in data and symbol in data["data"]:
                return {
                    "name": data["data"][symbol]["name"],
                    "price": data["data"][symbol]["quote"][currency]["price"],
                }
            else:
                return None

        except requests.exceptions.RequestException:
            return None
