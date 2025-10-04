class Connector:
    """Base class for data connectors."""

    def store_data(self, df, table_name):
        """Store data to the connector's destination."""
        raise NotImplementedError
