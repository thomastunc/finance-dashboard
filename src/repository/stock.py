from datetime import datetime

from src.model.stock import DeGiro
from src.repository import Repository


class DeGiroRepository(Repository):
    def __init__(self, config: dict, username: str, password: str, int_account: str, totp: str):
        super().__init__(config)
        self.degiro = DeGiro(username, password, int_account, totp)

    def get_and_store_stocks(self, source: str):
        df = self.degiro.retrieve_stocks()
        df = self.convert_currencies(df, ["purchase_value", "current_value", "portfolio_value"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())
        self.connector.store_data(df, self.STOCK)

    def get_and_store_account(self, source: str):
        df = self.degiro.retrieve_account()
        df = self.convert_currencies(df, ["balance"])

        df.insert(0, "source", source)
        df.insert(0, "date", datetime.now().date())

        self.connector.store_data(df, self.BANK)

    def logout(self):
        self.degiro.logout()
