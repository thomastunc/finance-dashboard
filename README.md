# Finance Dashboard

This project is designed for extracting financial data from various sources, e.g. bank accounts, stock providers, and
cryptocurrency wallets. With the ability to consolidate financial data into a storage service, like Google BigQuery.

You can run this code daily to extract the new values of your financial sources and store them in a database. This
allows you to analyze your financial data over time and gain insights into your financial health. You can also use the
data for other financial analysis tasks, e.g. budgeting, forecasting, and reporting. For example, I am using this to
visualize my net worth over time inside Looker Data Studio.

## Installation and Setup

To get started with this project, follow these steps:

1. Clone the repository:

   ```shell
   git clone https://github.com/thomastunc/finance-dashboard.git
   cd finance-dashboard
   ```

2. Install the required dependencies using Poetry:

   ```shell
   poetry install
   ```

3. Create a copy of the `.env.dist` file and name it `.env`:

   ```shell
   cp .env.dist .env
   ```

   Edit the values in the `.env` file to configure your environment variables according to your needs:

   ```shell
   nano .env
   ```

4. If you want to use GCP like me, Set up Google Cloud Platform (GCP) and the following resources:

    - Create a Google BigQuery dataset for storing the data.
    - Configure and set up a Google Compute Engine instance where you will run the Python scripts.

5. Copy the `src/template.py` file, which you can use as a base for your own data extraction script:

   ```shell
   cp src/template.py main.py
   ```


6. Customize the `main.py` file to meet your specific data extraction needs. This file acts as a starting point for your
   financial data extraction:

   ```shell
   nano main.py
   ```

7. Schedule the Python script to run daily on the Google Compute Engine instance using a cron job:

   ```shell
   crontab -e
   ```

   Add a line to schedule your script to run daily:

   ```shell
   0 0 * * * /usr/bin/python3 /path/to/your/main.py
   ```

## Usage

To use the Finance Dashboard, follow these steps:

1. Execute your customized Python script:

   ```shell
   python main.py
   ```

2. The script will extract financial data from your configured sources and store it in a connector (e.g. BigQuery).

3. Analyze and visualize your financial data, for example by connecting Looker Data Studio to your data source.

## Future Improvements

Some areas for potential improvement:

- **Additional Data Sources**: Expand the project to support more external sources for broader financial data coverage.
- **Additional Connectors**: Add more connectors to support additional data storage services.
- **Easier Installation and Configuration**: Enhance the setup process to make it even more user-friendly and
  streamlined.
- **Historical Data Retrieval**: Implement functionality to retrieve historical data from various sources for
  comprehensive financial analysis.

## Contributions

Contributions to the Finance Dashboard project are highly encouraged and welcome. If you have ideas, feature requests,
or code improvements, feel free to create a pull request or open an issue on the project's GitHub repository.

