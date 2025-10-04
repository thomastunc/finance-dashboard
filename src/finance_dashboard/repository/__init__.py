import logging
import traceback

from finance_dashboard.connector import Connector as Connector


class Repository:
    """Base repository class for financial data operations."""

    BANK = "bank"
    STOCK = "stock"
    CRYPTO = "crypto"

    def __init__(self, config: dict):
        """Initialize repository with configuration."""
        self.connector = config["connector"]
        self.converter = config["converter"]

    def convert_currencies(self, df, columns):
        """Convert specified columns to preferred currency using currency converter."""
        logger = logging.getLogger(__name__)
        preferred_currency = self.converter.ref_currency
        logger.debug(f"Converting currencies to preferred currency: {preferred_currency}")
        logger.debug(f"Supported currencies: {list(self.converter.currencies)}")

        conversion_count = 0
        for index, row in df.iterrows():
            try:
                current_currency = row["currency"]
                logger.debug(
                    f"Processing row {index}: Account '{row.get('name', 'Unknown')}' with currency {current_currency}"
                )

                if current_currency != preferred_currency:
                    # Check if the currency is supported by the converter
                    if current_currency not in self.converter.currencies:
                        logger.warning(
                            f"Currency {current_currency} is not supported by the currency converter. Skipping conversion for account '{row.get('name', 'Unknown')}'"
                        )
                        # Keep original values and add original columns for consistency
                        for column in columns:
                            df.at[index, f"original_{column}"] = row[column]
                        df.at[index, "original_currency"] = current_currency
                        continue

                    logger.debug(f"Converting row {index}: {current_currency} to {preferred_currency}")
                    for column in columns:
                        try:
                            original_value = row[column]
                            converted_value = self.converter.convert(
                                original_value, current_currency, preferred_currency
                            )
                            df.at[index, f"original_{column}"] = original_value
                            df.at[index, column] = round(converted_value, 2)
                            logger.debug(
                                f"Converted {column}: {original_value} {current_currency} -> {round(converted_value, 2)} {preferred_currency}"
                            )
                        except Exception as e:
                            error_details = {
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "file": __file__,
                                "function": "Repository.convert_currencies",
                                "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno,
                                "row_index": index,
                                "column": column,
                                "original_value": row[column],
                                "from_currency": current_currency,
                                "to_currency": preferred_currency,
                                "stack_trace": traceback.format_exc(),
                            }
                            logger.exception(
                                f"Error converting currency for row {index}, column {column}: {error_details}"
                            )
                            raise

                    df.at[index, "original_currency"] = current_currency
                    df.at[index, "currency"] = preferred_currency
                    conversion_count += 1
                else:
                    logger.debug(f"Row {index}: Currency already in preferred format ({preferred_currency})")

            except Exception as e:
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "file": __file__,
                    "function": "Repository.convert_currencies",
                    "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno,
                    "row_index": index,
                    "row_data": dict(row),
                    "stack_trace": traceback.format_exc(),
                }
                logger.exception(f"Error processing currency conversion for row {index}: {error_details}")
                raise

        logger.info(f"Currency conversion completed: {conversion_count} rows converted to {preferred_currency}")
        return df
