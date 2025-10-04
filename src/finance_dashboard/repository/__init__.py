import traceback
import logging
from currency_converter import CurrencyConverter
from finance_dashboard.connector import Connector


class Repository:
    BANK = "bank"
    STOCK = "stock"
    CRYPTO = "crypto"

    def __init__(self, config: dict):
        self.connector = config["connector"]
        self.converter = config["converter"]

    def convert_currencies(self, df, columns):
        logger = logging.getLogger(__name__)
        preferred_currency = self.converter.ref_currency
        logger.debug(f"Converting currencies to preferred currency: {preferred_currency}")

        conversion_count = 0
        for index, row in df.iterrows():
            try:
                if row["currency"] != preferred_currency:
                    logger.debug(f"Converting row {index}: {row['currency']} to {preferred_currency}")
                    for column in columns:
                        try:
                            original_value = row[column]
                            converted_value = self.converter.convert(original_value, row["currency"], preferred_currency)
                            df.at[index, f"original_{column}"] = original_value
                            df.at[index, column] = round(converted_value, 2)
                            logger.debug(f"Converted {column}: {original_value} {row['currency']} -> {round(converted_value, 2)} {preferred_currency}")
                        except Exception as e:
                            error_details = {
                                'error_type': type(e).__name__,
                                'error_message': str(e),
                                'file': __file__,
                                'function': 'Repository.convert_currencies',
                                'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                                'row_index': index,
                                'column': column,
                                'original_value': row[column],
                                'from_currency': row["currency"],
                                'to_currency': preferred_currency,
                                'stack_trace': traceback.format_exc()
                            }
                            logger.error(f"Error converting currency for row {index}, column {column}: {error_details}")
                            raise

                    df.at[index, "original_currency"] = row["currency"]
                    df.at[index, "currency"] = preferred_currency
                    conversion_count += 1
                else:
                    logger.debug(f"Row {index}: Currency already in preferred format ({preferred_currency})")
                    
            except Exception as e:
                error_details = {
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'file': __file__,
                    'function': 'Repository.convert_currencies',
                    'line_number': traceback.extract_tb(e.__traceback__)[-1].lineno,
                    'row_index': index,
                    'row_data': dict(row),
                    'stack_trace': traceback.format_exc()
                }
                logger.error(f"Error processing currency conversion for row {index}: {error_details}")
                raise

        logger.info(f"Currency conversion completed: {conversion_count} rows converted to {preferred_currency}")
        return df
