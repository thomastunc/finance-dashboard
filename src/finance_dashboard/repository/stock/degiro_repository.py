from datetime import datetime

from finance_dashboard.model.stock.degiro import DeGiro
from finance_dashboard.repository import Repository


class DeGiroRepository(Repository):
    """Repository for DeGiro stock trading platform data operations."""

    def __init__(self, config: dict, username: str, password: str, int_account: str, totp: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.degiro = DeGiro(username, password, int_account, totp, config.get("converter"))
        except Exception:
            self.logger.exception("Error while initializing DeGiro")
            raise

    def get_and_store_stocks(self, source: str):
        """Retrieve and store stock portfolio data from DeGiro."""
        try:
            self.logger.debug(f"[{source}] Starting stock retrieval from DeGiro")
            df = self.degiro.retrieve_stocks()

            # Enhanced debug logging for the raw data
            self.logger.debug(
                f"[{source}] Retrieved {len(df)} stocks with columns: {df.columns.tolist() if not df.empty else 'None'}"
            )
            if not df.empty:
                currencies = df["currency"].unique().tolist()
                self.logger.debug(f"[{source}] Currencies found in stock data: {currencies}")

                # Log each stock's details
                for idx, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}] Stock {idx}: {row['name']} ({row['symbol']}) | "
                        f"Amount: {row['amount']} | Purchase: {row['purchase_value']} | "
                        f"Current: {row['current_value']} | Portfolio: {row['portfolio_value']} | "
                        f"Currency: {row['currency']}"
                    )

            # Check if we need currency conversion (only if not all EUR)
            if not df.empty and not all(df["currency"] == "EUR"):
                self.logger.debug(f"[{source}] Converting currencies for stock data")
                df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

                # Log after conversion
                for idx, row in df.iterrows():
                    original_currency = row.get("original_currency", "N/A")
                    self.logger.debug(
                        f"[{source}] After conversion {idx}: {row['name']} | "
                        f"Portfolio: {row['portfolio_value']} {row['currency']} | "
                        f"Original Currency: {original_currency}"
                    )
            else:
                self.logger.debug(f"[{source}] All stock data already in EUR, skipping currency conversion")

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())
            self.connector.store_data(df, self.STOCK)
            self.logger.info(f"[{source}] Stocks retrieved and stored")
        except Exception:
            self.logger.exception("[{source}] Error while retrieving and storing stocks")
            self.logger.warning(f"[{source}] Failed to retrieve new stock data, no data will be stored")

    def get_and_store_account(self, source: str):
        """Retrieve and store account balance data from DeGiro."""
        try:
            self.logger.debug(f"[{source}] Starting account retrieval from DeGiro")
            df = self.degiro.retrieve_account()

            # Enhanced debug logging for account data
            if not df.empty:
                row = df.iloc[0]
                self.logger.debug(
                    f"[{source}] Account data: {row['name']} | "
                    f"Balance: {row['balance']} {row['currency']} | "
                    f"IBAN: {row['iban']}"
                )

            # Check if we need currency conversion (only if not EUR)
            if not df.empty and not all(df["currency"] == "EUR"):
                self.logger.debug(f"[{source}] Converting currencies for account data")
                df = self.convert_currencies(df, ["balance"])

                # Log after conversion
                row = df.iloc[0]
                original_balance = row.get("original_balance", "N/A")
                original_currency = row.get("original_currency", "N/A")
                self.logger.debug(
                    f"[{source}] After conversion: {row['name']} | "
                    f"Balance: {row['balance']} {row['currency']} | "
                    f"Original: {original_balance} {original_currency}"
                )
            else:
                self.logger.debug(f"[{source}] Account data already in EUR, skipping currency conversion")

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.BANK)
            self.logger.info(f"[{source}] Account retrieved and stored")
        except Exception:
            self.logger.exception("[{source}] Error while retrieving and storing account")
            self.logger.warning(f"[{source}] Failed to retrieve new account data, no data will be stored")

    def logout(self):
        """Logout from DeGiro session."""
        try:
            self.degiro.logout()
            self.logger.info("Logged out")
        except Exception:
            self.logger.exception("Error while logging out")
