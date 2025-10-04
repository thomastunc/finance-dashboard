import json
import math
from urllib.parse import quote

import pandas as pd
import requests

from finance_dashboard.model.crypto import Crypto


class Cosmos(Crypto):
    """Cosmos ecosystem cryptocurrency connector for retrieving wallet and pool data."""

    def __init__(self, coinmarketcap_api_key: str, api_url: str, lcd_url: str, rpc_url: str):
        super().__init__(coinmarketcap_api_key)
        self.api_url = api_url
        self.lcd_url = lcd_url
        self.rpc_url = rpc_url

    def retrieve_wallet(self, address: str, currency: str):
        """Retrieve wallet balances from Cosmos address."""
        balances = self.get_balances_from_address(address)
        rows = []

        for balance in balances:
            metadata = self.get_coin_metadata(denom=balance["denom"])
            amount = balance["amount"]

            if metadata:
                currency_metadata = self.get_crypto_currency_metadata(metadata["symbol"], currency)

                if currency_metadata is not None:
                    current_value = currency_metadata.get("price", 0)
                    if current_value is None:
                        current_value = 0
                    exponent = metadata.get("exponent", 0)
                    amount = float(amount) / math.pow(10, exponent)
                    portfolio_value = amount * current_value

                    if portfolio_value > 1:
                        rows.append(
                            {
                                "name": metadata["name"],
                                "type": "Balance",
                                "symbol": metadata["symbol"],
                                "amount": amount,
                                "current_value": current_value,
                                "portfolio_value": round(portfolio_value, 2),
                                "currency": currency,
                            }
                        )

        return pd.DataFrame(rows)

    def retrieve_osmosis_pools(self, address: str, currency: str):
        """Retrieve staking pool balances from Osmosis."""
        defis = self.get_balances_from_pool(address)
        rows = []

        for defi in defis:
            pool_id = defi["denom"].split("/")[-1]
            metadata = self.get_osmosis_pool_metadata(pool_id)
            amount = self.calculate_pool_amount(defi["denom"], defi["amount"])

            if metadata:
                currency_metadata = self.get_crypto_currency_metadata(metadata["secondary_symbol"], currency)

                if currency_metadata is not None:
                    current_value = currency_metadata.get("price", 0)
                    if current_value is None:
                        current_value = 0
                    exponent = metadata.get("exponent", 0)
                    amount = float(amount) / math.pow(10, exponent)
                    portfolio_value = amount * current_value

                    if portfolio_value > 1:
                        rows.append(
                            {
                                "name": f"{metadata['primary_symbol']} / {metadata['secondary_symbol']} Pool",
                                "type": "DeFi",
                                "symbol": f"{metadata['primary_symbol']}/{metadata['secondary_symbol']}",
                                "amount": amount,
                                "current_value": current_value,
                                "portfolio_value": round(portfolio_value, 2),
                                "currency": currency,
                            }
                        )

        return pd.DataFrame(rows)

    def get_balances_from_address(self, address: str):
        """Get balance data from a Cosmos address via LCD API."""
        responses = []

        endpoint = "/cosmos/bank/v1beta1/balances/"
        results = json.loads(requests.get(self.lcd_url + endpoint + address, timeout=60).content)
        responses += results["balances"]
        pagination = results["pagination"]["next_key"]

        while pagination is not None:
            results = json.loads(
                requests.get(
                    self.lcd_url + endpoint + "?pagination.key=" + quote(str(pagination)),
                    timeout=60,
                ).content
            )
            responses += results["balances"]
            pagination = results["pagination"]["next_key"]

        return responses

    def get_balances_from_pool(self, address: str):
        """Get staking pool delegation balances from Osmosis."""
        endpoint = "/osmosis/superfluid/v1beta1/total_delegation_by_delegator/"
        results = json.loads(requests.get(self.lcd_url + endpoint + address, timeout=60).content)
        return results["total_delegated_coins"]

    def get_coin_metadata(self, symbol: str | None = None, denom: str | None = None):
        """Get coin metadata from symbol or denomination."""
        if denom:
            endpoint = "/search/v1/symbol?denom="
            response = json.loads(requests.get(self.api_url + endpoint + denom, timeout=60).content)
            symbol = response.get("symbol", None)
        if symbol:
            endpoint = f"/tokens/v2/{symbol}"
            return json.loads(requests.get(self.api_url + endpoint, timeout=60).content)[0]
        return None

    def get_osmosis_pool_metadata(self, pool_id: str | None = None):
        """Get Osmosis pool metadata by pool ID."""
        if pool_id:
            endpoint = f"/pools/v2/{pool_id}"
            response = json.loads(requests.get(self.api_url + endpoint, timeout=60).content)

            metadata_primary_coin = response[0]
            metadata_secondary_coin = response[1]

            return {
                "primary_symbol": metadata_primary_coin["symbol"],
                "secondary_symbol": metadata_secondary_coin["symbol"],
                "exponent": 6,
            }
        return None

    def calculate_pool_amount(self, denom: str, amount: str):
        """Calculate actual pool amount using asset multiplier."""
        endpoint = "/osmosis/superfluid/v1beta1/asset_multiplier?denom="
        response = json.loads(requests.get(self.lcd_url + endpoint + denom, timeout=60).content)
        multiplier = response["osmo_equivalent_multiplier"]["multiplier"]
        return float(amount) * float(multiplier) * 2
