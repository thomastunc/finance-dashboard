def bank():
    """Return the schema definition for bank data tables."""
    return [
        {"name": "date", "type": "DATE"},
        {"name": "source", "type": "STRING"},
        {"name": "name", "type": "STRING"},
        {"name": "iban", "type": "STRING"},
        {"name": "balance", "type": "FLOAT"},
        {"name": "currency", "type": "STRING"},
        {"name": "original_balance", "type": "FLOAT"},
        {"name": "original_currency", "type": "STRING"},
    ]


def stock():
    """Return the schema definition for stock data tables."""
    return [
        {"name": "date", "type": "DATE"},
        {"name": "source", "type": "STRING"},
        {"name": "name", "type": "STRING"},
        {"name": "symbol", "type": "STRING"},
        {"name": "amount", "type": "INTEGER"},
        {"name": "purchase_value", "type": "FLOAT"},
        {"name": "current_value", "type": "FLOAT"},
        {"name": "portfolio_value", "type": "FLOAT"},
        {"name": "currency", "type": "STRING"},
        {"name": "original_purchase_value", "type": "FLOAT"},
        {"name": "original_current_value", "type": "FLOAT"},
        {"name": "original_portfolio_value", "type": "FLOAT"},
        {"name": "original_currency", "type": "STRING"},
    ]


def crypto():
    """Return the schema definition for crypto data tables."""
    return [
        {"name": "date", "type": "DATE"},
        {"name": "source", "type": "STRING"},
        {"name": "name", "type": "STRING"},
        {"name": "type", "type": "STRING"},
        {"name": "symbol", "type": "STRING"},
        {"name": "amount", "type": "FLOAT"},
        {"name": "current_value", "type": "FLOAT"},
        {"name": "portfolio_value", "type": "FLOAT"},
        {"name": "currency", "type": "STRING"},
        {"name": "original_current_value", "type": "FLOAT"},
        {"name": "original_portfolio_value", "type": "FLOAT"},
        {"name": "original_currency", "type": "STRING"},
    ]
