import pandas as pd
from coinbase.rest import RESTClient

from finance_dashboard.model.crypto import Crypto


class Coinbase(Crypto):
    """Coinbase cryptocurrency connector for retrieving wallet data."""

    def __init__(self, coinmarketcap_api_key: str, coinbase_key_file: str):
        super().__init__(coinmarketcap_api_key)
        self.client = RESTClient(key_file=coinbase_key_file)

    def retrieve_wallet(self, currency: str):
        """Retrieve wallet balances from Coinbase."""
        accounts = self.client.get_accounts(250)["accounts"]

        import json
        import logging

        logger = logging.getLogger(__name__)

        # Raw data logging
        logger.debug("=== FULL COINBASE API RESPONSE ===")
        logger.debug(f"Complete accounts response: {json.dumps(accounts, indent=2, default=str)}")
        logger.debug("=" * 50)

        rows = []

        for account in accounts:
            logger.debug(f"Processing account: {json.dumps(account, indent=2, default=str)}")
            amount = float(account["available_balance"]["value"])
            symbol = account["available_balance"]["currency"]
            metadata = self.get_crypto_currency_metadata(symbol, currency)
            logger.debug(f"Metadata for {symbol}: {json.dumps(metadata, indent=2, default=str)}")

            if metadata is not None:
                price = float(metadata.get("price") or 0)
                portfolio_value = amount * price

                if portfolio_value > 1:
                    rows.append(
                        {
                            "name": metadata["name"],
                            "type": "Balance",
                            "symbol": symbol,
                            "amount": amount,
                            "current_value": price,
                            "portfolio_value": round(portfolio_value, 2),
                            "currency": currency,
                        }
                    )

        return pd.DataFrame(rows)
