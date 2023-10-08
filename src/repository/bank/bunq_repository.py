from datetime import datetime

from src.repository import Repository
from src.model.bank.bunq import Bunq


class BunqRepository(Repository):

    def __init__(self, config: dict, api_key: str, configuration_file: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.bunq = Bunq(api_key, configuration_file)
        except Exception as e:
            self.logger.error(f"Error while initializing Bunq: {e}")

    def get_and_store_accounts(self, source: str):
        try:
            df = self.bunq.retrieve_accounts()
            df = self.convert_currencies(df, ["balance"])

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.connector.store_data(df, self.BANK)
            self.logger.info(f"[{source}] Accounts retrieved and stored")
        except Exception as e:
            self.logger.error(f"[{source}] Error while retrieving and storing accounts: {e}")
