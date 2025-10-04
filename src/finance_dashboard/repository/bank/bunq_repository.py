import traceback
from datetime import datetime

from finance_dashboard.model.bank.bunq import Bunq
from finance_dashboard.repository import Repository


class BunqRepository(Repository):
    """Repository for Bunq bank data operations."""

    def __init__(self, config: dict, api_key: str, configuration_file: str):
        super().__init__(config)
        self.logger = config["logger"].get_logger(__name__)

        try:
            self.logger.info(f"Initializing Bunq with configuration file: {configuration_file}")
            self.bunq = Bunq(api_key, configuration_file)
            self.logger.info("Bunq initialization successful")
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file": __file__,
                "function": "BunqRepository.__init__",
                "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno,
                "stack_trace": traceback.format_exc(),
            }
            self.logger.exception(f"Error while initializing Bunq: {error_details}")
            raise  # Re-raise the exception to prevent silent failures

    def get_and_store_accounts(self, source: str):
        """Retrieve and store Bunq account data."""
        self.logger.info(f"[{source}] Starting account retrieval and storage process")
        try:
            self.logger.debug(f"[{source}] Retrieving accounts from Bunq")
            df = self.bunq.retrieve_accounts_safe()
            self.logger.debug(f"[{source}] Successfully retrieved {len(df)} accounts from Bunq")

            # Debug log the raw data received
            if not df.empty:
                self.logger.debug(f"[{source}] Raw account data columns: {df.columns.tolist()}")
                for idx, row in df.iterrows():
                    self.logger.debug(
                        f"[{source}] Account {idx}: {row['name']} | Balance: {row['balance']} {row['currency']} | IBAN: {row['iban']}"
                    )

            self.logger.debug(f"[{source}] Converting currencies for balance columns")
            df = self.convert_currencies(df, ["balance"])

            # Debug log after currency conversion
            if not df.empty:
                for idx, row in df.iterrows():
                    original_balance = row.get("original_balance", "N/A")
                    original_currency = row.get("original_currency", "N/A")
                    self.logger.debug(
                        f"[{source}] After conversion {idx}: {row['name']} | Balance: {row['balance']} {row['currency']} | Original: {original_balance} {original_currency}"
                    )

            df.insert(0, "source", source)
            df.insert(0, "date", datetime.now().date())

            self.logger.debug(f"[{source}] Storing data to {self.BANK} table")
            self.connector.store_data(df, self.BANK)
            self.logger.info(f"[{source}] Accounts retrieved and stored successfully")
        except Exception as e:
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "file": __file__,
                "function": "BunqRepository.get_and_store_accounts",
                "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno,
                "source": source,
                "stack_trace": traceback.format_exc(),
            }
            self.logger.exception(f"[{source}] Error while retrieving and storing accounts: {error_details}")
            self.logger.warning(f"[{source}] Failed to retrieve new data, no data will be stored")
