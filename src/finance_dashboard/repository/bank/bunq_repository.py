import traceback
from datetime import datetime

from finance_dashboard.repository import Repository
from finance_dashboard.model.bank.bunq import Bunq


class BunqRepository(Repository):
    def __init__(self, config: dict, api_key: str, configuration_file: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.logger.info(f"Initializing Bunq with configuration file: {configuration_file}")
            self.bunq = Bunq(api_key, configuration_file)
            self.logger.info("Bunq initialization successful")
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'BunqRepository.__init__',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'stack_trace': traceback.format_exc()
            }
            self.logger.error(f"Error while initializing Bunq: {error_details}")
            raise  # Re-raise the exception to prevent silent failures

    def get_and_store_accounts(self, source: str):
        self.logger.info(f"[{source}] Starting account retrieval and storage process")
        try:
            self.logger.debug(f"[{source}] Retrieving accounts from Bunq")
            df = self.bunq.retrieve_accounts_safe()
            self.logger.debug(f"[{source}] Successfully retrieved {len(df)} accounts from Bunq")
            
            self.logger.debug(f"[{source}] Converting currencies for balance columns")
            df = self.convert_currencies(df, ["balance"])
            
            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.logger.debug(f"[{source}] Storing data to {self.BANK} table")
            self.connector.store_data(df, self.BANK)
            self.logger.info(f"[{source}] Accounts retrieved and stored successfully")
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'BunqRepository.get_and_store_accounts',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'source': source,
                'stack_trace': traceback.format_exc()
            }
            self.logger.error(f"[{source}] Error while retrieving and storing accounts: {error_details}")
            self.logger.warning(f"[{source}] Failed to retrieve new data, no data will be stored")
