import os
import socket
import warnings
import pandas as pd
import traceback
import logging
import time

from bunq import ApiEnvironmentType
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.model.generated.endpoint import MonetaryAccountApiObject


class Bunq:
    def __init__(self, api_key: str, configuration_file: str):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.configuration_file = configuration_file
        
        try:
            self.logger.info(f"Creating or restoring API context for configuration file: {configuration_file}")
            self.api_context = self.create_or_restore_api_context()
            self.logger.info("Bunq API context initialized successfully")
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'Bunq.__init__',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'configuration_file': configuration_file,
                'stack_trace': traceback.format_exc()
            }
            self.logger.error(f"Failed to initialize Bunq API context: {error_details}")
            raise

    def retrieve_accounts(self):
        try:
            self.logger.debug("Starting account retrieval process")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                self.logger.debug("Loading BunqContext with API context")
                BunqContext.load_api_context(self.api_context)

                self.logger.debug("Fetching monetary accounts from Bunq API")
                
                # Try to get accounts with error handling for malformed API responses
                try:
                    monetary_accounts = MonetaryAccountApiObject.list(params={"count": "100"})
                    self.logger.debug(f"Retrieved {len(monetary_accounts.value)} monetary accounts from API")
                except TypeError as e:
                    if "float() argument must be a string or a real number, not 'NoneType'" in str(e):
                        self.logger.warning("Bunq API returned malformed data with null values. Trying with smaller batch size...")
                        # Try with smaller batch size to see if it helps
                        monetary_accounts = MonetaryAccountApiObject.list(params={"count": "50"})
                        self.logger.debug(f"Retrieved {len(monetary_accounts.value)} monetary accounts with smaller batch")
                    else:
                        raise
                
                rows = []

                for i, monetary_account in enumerate(monetary_accounts.value):
                    try:
                        self.logger.debug(f"Processing account {i + 1}/{len(monetary_accounts.value)}")
                        account = self.get_account_from_type(monetary_account)

                        if account is not None and account.status == "ACTIVE":
                            iban = self.get_alias(account)
                            self.logger.debug(f"Found active account: {account.description} (IBAN: {iban})")

                            # Handle potential null values in balance and currency
                            balance_value = 0.0
                            if account.balance and hasattr(account.balance, 'value') and account.balance.value is not None:
                                try:
                                    balance_value = float(account.balance.value)
                                except (ValueError, TypeError) as e:
                                    self.logger.warning(f"Invalid balance value for account {account.description}: {account.balance.value}. Using 0.0")
                                    balance_value = 0.0
                            
                            currency = account.currency if hasattr(account, 'currency') and account.currency else "EUR"
                            
                            rows.append({
                                "name": account.description if hasattr(account, 'description') and account.description else f"Account {i+1}",
                                "iban": iban,
                                "balance": balance_value,
                                "currency": currency
                            })
                        else:
                            status = account.status if account and hasattr(account, 'status') else "None"
                            self.logger.debug(f"Skipping inactive or invalid account (status: {status})")
                            
                    except Exception as e:
                        error_details = {
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'file': __file__,
                            'function': 'Bunq.retrieve_accounts',
                            'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                            'account_index': i,
                            'stack_trace': traceback.format_exc()
                        }
                        self.logger.error(f"Error processing account {i + 1}: {error_details}")
                        continue  # Continue with next account

                self.logger.info(f"Successfully processed {len(rows)} active accounts")
                return pd.DataFrame(rows)
                
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'Bunq.retrieve_accounts',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'stack_trace': traceback.format_exc()
            }
            self.logger.error(f"Failed to retrieve accounts: {error_details}")
            raise

    def create_or_restore_api_context(self):
        try:
            if os.path.isfile(self.configuration_file):
                self.logger.debug(f"Configuration file exists, restoring API context from: {self.configuration_file}")
                api_context = ApiContext.restore(self.configuration_file)
                self.logger.info("API context restored successfully from existing configuration")
            else:
                self.logger.debug(f"Configuration file not found, creating new API context")
                hostname = socket.gethostname()
                self.logger.debug(f"Using hostname: {hostname}")
                api_context = ApiContext.create(ApiEnvironmentType.PRODUCTION, self.api_key, hostname)  # type: ignore
                self.logger.debug(f"Saving new API context to: {self.configuration_file}")
                api_context.save(self.configuration_file)
                self.logger.info("New API context created and saved successfully")

            return api_context
            
        except Exception as e:
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'Bunq.create_or_restore_api_context',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'configuration_file': self.configuration_file,
                'file_exists': os.path.isfile(self.configuration_file),
                'stack_trace': traceback.format_exc()
            }
            self.logger.error(f"Failed to create or restore API context: {error_details}")
            raise

    def retrieve_accounts_safe(self):
        """
        Safer account retrieval method that handles API response issues
        Patches the Bunq SDK to handle null values gracefully
        """
        try:
            # Monkey patch the Bunq SDK's float adapter to handle null values
            self._patch_bunq_float_adapter()
            return self.retrieve_accounts()
        except Exception as e:
            self.logger.error(f"Account retrieval failed: {e}")
            # Return empty DataFrame as fallback
            return pd.DataFrame(columns=["name", "iban", "balance", "currency"])
        finally:
            # Restore original float adapter
            self._restore_bunq_float_adapter()
    
    def _patch_bunq_float_adapter(self):
        """
        Monkey patch the Bunq SDK's float adapter to handle null values
        """
        try:
            from bunq.sdk.json import float_adapter
            
            # Store the original deserialize method
            self._original_float_deserialize = float_adapter.FloatAdapter.deserialize
            
            # Create a safer version that handles null values
            def safe_float_deserialize(cls, target_class, string):
                _ = target_class  # Keep the same signature as original
                
                if string is None:
                    self.logger.debug("Converting null float value to 0.0")
                    return 0.0
                try:
                    return float(string)
                except (ValueError, TypeError):
                    self.logger.warning(f"Could not convert '{string}' to float, using 0.0")
                    return 0.0
            
            # Patch the method
            float_adapter.FloatAdapter.deserialize = classmethod(safe_float_deserialize)
            self.logger.debug("Successfully patched Bunq float adapter to handle null values")
            
        except Exception as e:
            self.logger.warning(f"Could not patch Bunq float adapter: {e}")
    
    def _restore_bunq_float_adapter(self):
        """
        Restore the original Bunq SDK float adapter
        """
        try:
            if hasattr(self, '_original_float_deserialize'):
                from bunq.sdk.json import float_adapter
                float_adapter.FloatAdapter.deserialize = self._original_float_deserialize
                self.logger.debug("Restored original Bunq float adapter")
        except Exception as e:
            self.logger.warning(f"Could not restore original float adapter: {e}")

    @staticmethod
    def get_alias(account):
        try:
            for alias in account.alias:
                if alias.type_ == "IBAN":
                    return alias.value
            
            # Log if no IBAN alias is found
            logger = logging.getLogger(__name__)
            logger.warning(f"No IBAN alias found for account: {account.description if hasattr(account, 'description') else 'Unknown'}")
            return None
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'Bunq.get_alias',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'stack_trace': traceback.format_exc()
            }
            logger.error(f"Error getting alias for account: {error_details}")
            return None

    @staticmethod
    def get_account_from_type(monetary_account: MonetaryAccountApiObject):
        try:
            if monetary_account.MonetaryAccountBank is not None:
                return monetary_account.MonetaryAccountBank
            elif monetary_account.MonetaryAccountSavings is not None:
                return monetary_account.MonetaryAccountSavings
            elif monetary_account.MonetaryAccountJoint is not None:
                return monetary_account.MonetaryAccountJoint
            elif monetary_account.MonetaryAccountLight is not None:
                return monetary_account.MonetaryAccountLight
            
            # Log if no known account type is found
            logger = logging.getLogger(__name__)
            logger.warning("Unknown monetary account type encountered")
            return None
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
                'file': __file__,
                'function': 'Bunq.get_account_from_type',
                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                'stack_trace': traceback.format_exc()
            }
            logger.error(f"Error determining account type: {error_details}")
            return None
