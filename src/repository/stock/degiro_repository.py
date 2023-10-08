from datetime import datetime

from src.model.stock.degiro import DeGiro
from src.repository import Repository


class DeGiroRepository(Repository):
    def __init__(self, config: dict, username: str, password: str, int_account: str, totp: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.degiro = DeGiro(username, password, int_account, totp)
        except Exception as e:
            self.logger.error(f"Error while initializing DeGiro: {e}")

    def get_and_store_stocks(self, source: str):
        try:
            df = self.degiro.retrieve_stocks()
            df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())
            self.connector.store_data(df, self.STOCK)
            self.logger.info(f"[{source}] Stocks retrieved and stored")
        except Exception as e:
            self.logger.error(f"[{source}] Error while retrieving and storing stocks: {e}")

    def get_and_store_account(self, source: str):
        try:
            df = self.degiro.retrieve_account()
            df = self.convert_currencies(df, ["balance"])

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.BANK)
            self.logger.info(f"[{source}] Account retrieved and stored")
        except Exception as e:
            self.logger.error(f"[{source}] Error while retrieving and storing account: {e}")

    def logout(self):
        try:
            self.degiro.logout()
            self.logger.info("Logged out")
        except Exception as e:
            self.logger.error(f"Error while logging out: {e}")
