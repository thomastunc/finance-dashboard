# Finance Dashboard 📊

A comprehensive personal finance data aggregation tool that automatically collects and centralizes financial data from multiple sources into Google BigQuery for analysis and visualization.

## 🌟 Features

- **Multi-Source Data Collection**: Supports banks (Bunq), brokers (DeGiro), crypto exchanges (Coinbase), and Web3 wallets
- **Flexible Pipeline Configuration**: YAML-based configuration for easy customization
- **Multiple Accounts**: Support for multiple accounts per source type (e.g., 2 Bunq accounts)
- **Automated Currency Conversion**: Converts all amounts to your preferred currency
- **BigQuery Integration**: Stores data in Google BigQuery for powerful analytics
- **Daily Logging**: Organized log files by date in the `logs/` directory
- **Error Handling & Notifications**: Comprehensive logging with optional Telegram notifications
- **Scheduled Execution**: Designed for daily automated runs via cron jobs

## 🚀 Installation and Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- Google Cloud Platform account (for BigQuery)

### Quick Start

1. **Clone the repository:**

   ```bash
   git clone https://github.com/thomastunc/finance-dashboard.git
   cd finance-dashboard
   ```

2. **Install dependencies:**

   ```bash
   uv sync
   ```

3. **Configure environment variables:**

   ```bash
   cp .env.dist .env
   # Edit .env with your API keys and configuration
   nano .env
   ```

4. **Configure your pipeline:**

   ```bash
   cp examples/pipeline-simple.yml pipeline.yml
   # Edit pipeline.yml to enable/disable sources and configure accounts
   nano pipeline.yml
   ```

5. **Set up Google Cloud BigQuery:**

   - Create a Google Cloud Project
   - Enable the BigQuery API
   - Create a dataset for storing financial data
   - Download service account credentials to `config/service_account.json`

6. **Run the application:**

   ```bash
   uv run finance-dashboard --config pipeline.yml
   ```

## ⚙️ Configuration

### Pipeline Configuration (YAML)

The pipeline is configured using a YAML file that defines which data sources to collect and how to process them.

**Example pipeline.yml:**

```yaml
# Global Settings
global:
  log_level: INFO
  preferred_currency: EUR

# Database Configuration
database:
  connector: bigquery
  credentials_path: config/service_account.json
  project_id: your-project-id
  schema_id: your-schema-id
  location: europe-west4
  table_names:
    accounts: bank-accounts
    stocks: stocks
    crypto: crypto
    total: total

# Logging
logging:
  type: telegram  # Options: telegram, console, file
  telegram:
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
    send_summary: true
    dashboard_url: https://your-dashboard-url.com

# Bank Accounts
bank:
  enabled: true
  accounts:
    - name: Bunq Personal
      type: bunq
      api_key_env: BUNQ_API_KEY
      configuration_file: config/bunq_context.json

# Stock Accounts
stock:
  enabled: true
  accounts:
    - name: DeGiro
      type: degiro
      username_env: DEGIRO_USERNAME
      password_env: DEGIRO_PASSWORD
      int_account_env: DEGIRO_INT_ACCOUNT
      totp_env: DEGIRO_TOTP

# Crypto Accounts
crypto:
  enabled: true
  coinmarketcap_api_key_env: COINMARKETCAP_API_KEY
  moralis_api_key_env: MORALIS_API_KEY
  accounts:
    - name: Coinbase
      type: coinbase
      key_file: config/cdp_api_key.json
    
    - name: Metamask
      type: web3
      wallet_address_env: METAMASK_WALLET_ADDRESS
      chains:
        - eth
        - polygon
```

### Multiple Accounts

You can easily add multiple accounts of the same type:

```yaml
bank:
  enabled: true
  accounts:
    - name: Bunq Personal
      type: bunq
      api_key_env: BUNQ_API_KEY_PERSONAL
      configuration_file: config/bunq_context_personal.json
    
    - name: Bunq Business
      type: bunq
      api_key_env: BUNQ_API_KEY_BUSINESS
      configuration_file: config/bunq_context_business.json
```

### Configuration Values

**Direct values** (stored in pipeline.yml):
```yaml
credentials_path: config/service_account.json
project_id: your-project-id
schema_id: your-schema-id
location: europe-west4
dashboard_url: https://your-dashboard-url.com
```

**Environment variables** (referenced with `_env` suffix, stored in .env):
```yaml
# In pipeline.yml
api_key_env: BUNQ_API_KEY
bot_token_env: TELEGRAM_BOT_TOKEN
```
```bash
# In .env file
BUNQ_API_KEY=your-actual-api-key-here
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

## 💻 Usage

### Manual Execution

Run the dashboard manually to collect current financial data:

```bash
finance-dashboard --config pipeline.yml
```

### Validate Configuration

Check your configuration without running the pipeline:

```bash
finance-dashboard --config pipeline.yml --validate-only
```

### Custom Configuration File

You can use different configuration files for different setups:

```bash
finance-dashboard --config production.yml
finance-dashboard --config testing.yml
```

### Automated Scheduling

For daily automated data collection, set up a cron job:

```bash
crontab -e
```

Add this line to run daily at midnight:

```bash
0 0 * * * cd /path/to/finance-dashboard && uv run finance-dashboard --config pipeline.yml
```

### Monitoring

- **Logs**: Check daily log files in the `logs/` directory
- **Telegram**: Receive error notifications via Telegram (if configured)
- **Daily Summary**: Get a daily summary of your financial portfolio via Telegram (optional)
- **BigQuery**: Monitor data in your BigQuery dataset

### Daily Summary Feature 📊

The dashboard can automatically send a daily summary to Telegram after each data collection run.

**To enable the daily summary:**

Configure the logging section in your `pipeline.yml`:

```yaml
logging:
  type: telegram
  telegram:
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID
    send_summary: true
    dashboard_url: https://your-dashboard-url.com
```

- Set `send_summary: true` to enable daily summaries
- Optionally set `dashboard_url` to include a clickable link in the message
- Make sure the environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in your `.env` file

Example summary message:
```
📊 Daily Summary

💰 Total: €50.000
▲ €500 (+1.01%)

🏦 bank-accounts: €10.000
▲ €100 (+1.00%)

📈 stocks: €25.000
🔻 €300 (-1.21%)

🪙 crypto: €15.000
▲ €100 (+0.67%)

🔗 Open Dashboard
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal financial data aggregation only. Always:

- Keep your API keys and credentials secure
- Review the code before running
- Use at your own risk
- Comply with your financial institutions' terms of service

