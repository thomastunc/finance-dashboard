from currency_converter import CurrencyConverter
from src.connector import Connector


class Repository:
    BANK = "bank"
    STOCK = "stock"
    CRYPTO = "crypto"

    ATTEMPTS = 3
    DELAY = 10

    def __init__(self, config: dict):
        self.connector = config["connector"]
        self.converter = config["converter"]

    def convert_currencies(self, df, columns):
        preferred_currency = self.converter.ref_currency

        for index, row in df.iterrows():
            if row["currency"] != preferred_currency:
                for column in columns:
                    converted_value = self.converter.convert(row[column], row["currency"], preferred_currency)
                    df.at[index, f"original_{column}"] = row[column]
                    df.at[index, column] = round(converted_value, 2)

                df.at[index, "original_currency"] = row["currency"]
                df.at[index, "currency"] = preferred_currency

        return df
