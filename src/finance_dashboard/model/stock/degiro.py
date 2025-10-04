import logging

import pandas as pd
from degiro_connector.trading.api import API
from degiro_connector.trading.models.account import UpdateOption, UpdateRequest
from degiro_connector.trading.models.credentials import Credentials


class DeGiro:
    """DeGiro trading platform connector for retrieving stock and account data."""

    def __init__(self, username: str, password: str, int_account: str, totp: str, currency_converter=None):
        self.trading_api = API(
            credentials=Credentials(
                username=username,
                password=password,
                int_account=int(int_account),
                totp_secret_key=totp,
            )
        )
        self.trading_api.connect()
        self.currency_converter = currency_converter

    def search_stock(self, product_id: str):
        """Search for stock information by product ID."""
        products_info = self.trading_api.get_products_info(
            product_list=[product_id],
            raw=True,
        )

        import json
        import logging

        logger = logging.getLogger(__name__)
        logger.debug("=== FULL DEGIRO PRODUCT INFO API RESPONSE ===")
        logger.debug(f"Product ID: {product_id}")
        logger.debug(f"Full API Response: {json.dumps(products_info, indent=2, default=str)}")
        logger.debug("=" * 50)

        return products_info

    def retrieve_stocks(self):
        """Retrieve current stock portfolio holdings."""
        update = self.trading_api.get_update(
            request_list=[
                UpdateRequest(
                    option=UpdateOption.PORTFOLIO,
                    last_updated=0,
                ),
            ],
            raw=True,
        )

        import logging

        logger = logging.getLogger(__name__)

        portfolio_df = pd.DataFrame(update["portfolio"]["value"])
        rows = []

        for item in portfolio_df.index:
            item_metadata = {entry["name"]: entry.get("value", None) for entry in portfolio_df["value"][item]}
            item_amount = int(item_metadata["size"])

            if item_metadata["positionType"] == "PRODUCT" and item_amount > 0:
                product_id = str(portfolio_df["id"][item])
                stock_metadata = self.search_stock(product_id)

                currency = stock_metadata["data"][product_id]["currency"]
                purchase_value = item_metadata["breakEvenPrice"]
                current_value = item_metadata["price"]
                portfolio_value = item_metadata["value"]

                # Bereken de echte marktwaarde: aantal x huidige prijs
                original_market_value = item_amount * current_value
                original_currency = currency

                # Converteer naar EUR als er een currency converter beschikbaar is
                if self.currency_converter and original_currency != "EUR":
                    try:
                        converted_value = self.currency_converter.convert(
                            original_market_value, original_currency, "EUR"
                        )
                        converted_currency = "EUR"
                    except Exception as e:
                        # Als conversie faalt, gebruik originele waarde
                        converted_value = original_market_value
                        converted_currency = original_currency
                        logger.warning(f"Currency conversion failed for {original_currency} to EUR: {e}")
                else:
                    converted_value = original_market_value
                    converted_currency = original_currency

                # Show parsed values without override
                stock_name = stock_metadata["data"][product_id]["name"]

                logger.debug(f"DeGiro Stock: {stock_name}")
                logger.debug(f"  API Currency: {currency}")
                logger.debug(f"  Purchase Value: {purchase_value}")
                logger.debug(f"  Current Value: {current_value}")
                logger.debug(f"  Portfolio Value: {portfolio_value}")
                logger.debug(f"  Real Market Value: {original_market_value} {original_currency}")
                logger.debug(f"  Converted Value: {converted_value:.2f} {converted_currency}")
                logger.debug(f"  Product ID: {product_id}")

                rows.append(
                    {
                        "name": stock_metadata["data"][product_id]["name"],
                        "symbol": stock_metadata["data"][product_id]["symbol"],
                        "amount": item_amount,
                        "purchase_value": purchase_value,
                        "current_value": current_value,
                        "portfolio_value": round(converted_value, 2),  # Gebruik geconverteerde waarde
                        "original_portfolio_value": round(original_market_value, 2),
                        "original_currency": original_currency,
                        "currency": converted_currency,  # Nu altijd EUR (of origineel als conversie faalt)
                    }
                )

        # Toon totaal portfolio overzicht
        total_stocks = len(rows)

        # Groepeer per originele valuta voor details
        usd_stocks = [row for row in rows if row["original_currency"] == "USD"]
        eur_stocks = [row for row in rows if row["original_currency"] == "EUR"]

        total_usd_market_value = sum(row["original_portfolio_value"] for row in usd_stocks)
        total_eur_market_value = sum(row["original_portfolio_value"] for row in eur_stocks)

        # Totaal portfolio waarde in EUR (na conversie)
        total_portfolio_eur = sum(row["portfolio_value"] for row in rows)

        logger.debug("=" * 80)
        logger.debug("COMPLETE DEGIRO PORTFOLIO SUMMARY:")
        logger.debug(f"Total number of different stocks: {total_stocks}")
        logger.debug(f"TOTAL PORTFOLIO VALUE (EUR): {total_portfolio_eur:,.2f} EUR")
        logger.debug(f"USD Market Value: {total_usd_market_value:,.2f} USD")
        logger.debug(f"EUR Market Value: {total_eur_market_value:,.2f} EUR")
        logger.debug("=" * 80)

        logger.info(f"DeGiro retrieved {len(rows)} stocks")
        return pd.DataFrame(rows)

    def retrieve_account(self):
        """Retrieve account balance information."""
        update = self.trading_api.get_update(
            request_list=[
                UpdateRequest(
                    option=UpdateOption.TOTAL_PORTFOLIO,
                    last_updated=0,
                ),
            ],
            raw=True,
        )

        client_details_table = self.trading_api.get_client_details()

        logger = logging.getLogger(__name__)

        total_portfolio_df = pd.DataFrame(update["totalPortfolio"])
        total_portfolio_metadata = {entry["name"]: entry.get("value", None) for entry in total_portfolio_df["value"]}

        logger.debug("Total portfolio metadata retrieved for DeGiro account")

        account_currency = total_portfolio_metadata["cashFundCompensationCurrency"]
        account_balance = total_portfolio_metadata["totalCash"]

        logger.debug(f"DeGiro Account - Currency: {account_currency}, Total Cash: {account_balance}")
        logger.debug(f"  IBAN: {client_details_table['data']['flatexBankAccount']['iban']}")

        rows = [
            {
                "name": "Flatex",
                "iban": client_details_table["data"]["flatexBankAccount"]["iban"],
                "balance": account_balance,
                "currency": account_currency,
            }
        ]

        logger.info(f"DeGiro account data retrieved with currency: {account_currency}")
        return pd.DataFrame(rows)

    def logout(self):
        """Logout from DeGiro session."""
        self.trading_api.logout()
