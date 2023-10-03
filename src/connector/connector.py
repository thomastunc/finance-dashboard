import pandas_gbq


class Connector:
    def store_data(self, df, metadata):
        raise NotImplementedError


class BigQueryConnector(Connector):
    def __init__(self, credentials, project_id):
        self.credentials = credentials
        self.project_id = project_id

    def store_data(self, df, metadata):
        schema_id = metadata['schema_id']
        table_id = metadata['table_id']

        pandas_gbq.to_gbq(
            df,
            destination_table=f"{self.project_id}.{schema_id}.{table_id}",
            if_exists='append',
            project_id=self.project_id,
            credentials=self.credentials,
            table_schema=[{'name': 'date', 'type': 'DATE'}],
            progress_bar=False
        )
