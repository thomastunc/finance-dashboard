import os
import socket
import warnings
import pandas as pd

from bunq import ApiEnvironmentType
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.model.generated.endpoint import MonetaryAccount


class Bunq:
    def __init__(self, api_key: str, configuration_file: str):
        self.api_key = api_key
        self.configuration_file = configuration_file
        self.api_context = self.create_or_restore_api_context()

    def retrieve_accounts(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            BunqContext.load_api_context(self.api_context)

            monetary_accounts = MonetaryAccount.list(params={"count": "100"})
            rows = []

            for monetary_account in monetary_accounts.value:
                account = self.get_account_from_type(monetary_account)

                if account is not None and account.status == "ACTIVE":
                    iban = self.get_alias(account)

                    rows.append({
                        "name": account.description,
                        "iban": iban,
                        "balance": float(account.balance.value),
                        "currency": account.currency
                    })

            return pd.DataFrame(rows)

    def create_or_restore_api_context(self):
        if os.path.isfile(self.configuration_file):
            api_context = ApiContext.restore(self.configuration_file)
        else:
            api_context = ApiContext.create(ApiEnvironmentType.PRODUCTION, self.api_key, socket.gethostname())
            api_context.save(self.configuration_file)

        return api_context

    @staticmethod
    def get_alias(account):
        for alias in account.alias:
            if alias.type_ == "IBAN":
                return alias.value

        return None

    @staticmethod
    def get_account_from_type(monetary_account: MonetaryAccount):
        if monetary_account.MonetaryAccountBank is not None:
            return monetary_account.MonetaryAccountBank
        elif monetary_account.MonetaryAccountSavings is not None:
            return monetary_account.MonetaryAccountSavings
        elif monetary_account.MonetaryAccountJoint is not None:
            return monetary_account.MonetaryAccountJoint
        elif monetary_account.MonetaryAccountLight is not None:
            return monetary_account.MonetaryAccountLight
        return None
