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

## 🏗️ Architecture

```
Finance Dashboard
├── Data Sources
│   ├── 🏦 Bunq (Banking)
│   ├── 📈 DeGiro (Stocks)
│   ├── 💰 Coinbase (Crypto Exchange)
│   └── 🌐 Web3 Wallets (DeFi)
├── Processing Layer
│   ├── Currency Conversion
│   ├── Data Validation
│   └── Error Handling
└── Storage & Analytics
    ├── Google BigQuery
    └── Looker Studio
```

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

3. **Configure environment:**

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
   finance-dashboard --config pipeline.yml
   # OR
   python -m finance_dashboard --config pipeline.yml
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
0 0 * * * cd /path/to/finance-dashboard && /path/to/.venv/bin/finance-dashboard --config pipeline.yml
```

### Monitoring

- **Logs**: Check daily log files in the `logs/` directory
- **Telegram**: Receive error notifications via Telegram (if configured)
- **Daily Summary**: Get a daily summary of your financial portfolio via Telegram (optional)
- **BigQuery**: Monitor data in your BigQuery dataset

### Daily Summary Feature 📊

The dashboard can automatically send a daily summary to Telegram after each data collection run.

**To enable the daily summary:**

1. Set `TELEGRAM_SEND_SUMMARY=true` in your `.env` file
2. Optionally set `DASHBOARD_URL` to include a clickable link in the message
3. Make sure `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are configured

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

## 📁 Project Structure
```

## � Migration from Old main.py

If you're upgrading from an older version that used a custom `main.py` file:

### Step 1: Backup Your Configuration

```bash
# Backup your old main.py if needed
cp main.py main.py.backup
```

### Step 2: Create Pipeline Configuration

```bash
# Copy the simple example
cp examples/pipeline-simple.yml pipeline.yml

# Or the full example with multiple accounts
cp examples/pipeline-full.yml pipeline.yml
```

### Step 3: Configure Your Sources

Edit `pipeline.yml` and enable/configure the sources you were using in your old `main.py`.

**Old way (main.py):**
```python
def run(self):
    self._collect_bunq_data()
    self._collect_degiro_data()
    self._collect_web3_data()
```

**New way (pipeline.yml):**
```yaml
bank:
  enabled: true
  accounts:
    - name: Bunq
      type: bunq
      api_key_env: BUNQ_API_KEY
      configuration_file: config/bunq_context.json

stock:
  enabled: true
  accounts:
    - name: DeGiro
      type: degiro
      username_env: DEGIRO_USERNAME
      password_env: DEGIRO_PASSWORD
      int_account_env: DEGIRO_INT_ACCOUNT
      totp_env: DEGIRO_TOTP

crypto:
  enabled: true
  moralis_api_key_env: MORALIS_API_KEY
  accounts:
    - name: Metamask
      type: web3
      wallet_address_env: METAMASK_WALLET_ADDRESS
      chains:
        - eth
        - polygon
```

### Step 4: Update Your .env File

Make sure all the environment variables referenced in your `pipeline.yml` exist in your `.env` file.
See `.env.dist` for examples.

### Step 5: Test Your Configuration

```bash
# Validate the configuration
finance-dashboard --config pipeline.yml --validate-only

# Test run
finance-dashboard --config pipeline.yml
```

### Step 6: Update Cron Jobs

If you have automated scheduling, update your cron job:

**Old:**
```bash
0 0 * * * cd /path/to/finance-dashboard && python main.py
```

**New:**
```bash
0 0 * * * cd /path/to/finance-dashboard && /path/to/.venv/bin/finance-dashboard --config pipeline.yml
```

### Benefits of the New System

✅ **No Code Changes**: Configure everything in YAML  
✅ **Multiple Accounts**: Easy to add multiple accounts per source  
✅ **Environment Variables**: Clear separation of config and credentials  
✅ **Validation**: Built-in configuration validation  
✅ **CLI Tool**: Proper command-line interface with help text  

## 📁 Project Structure

```
finance-dashboard/
├── config/                      # Configuration files (gitignored)
│   ├── bunq_context.json
│   ├── cdp_api_key.json
│   └── service_account.json
├── examples/                    # Example configurations
│   ├── pipeline-simple.yml      # Simple example
│   └── pipeline-full.yml        # Full example with multiple accounts
├── logs/                        # Log files (gitignored)
├── src/finance_dashboard/       # Main package
│   ├── __main__.py             # CLI entrypoint
│   ├── main.py                 # Application logic
│   ├── pipeline_config.py      # Pipeline configuration parser
│   ├── connector/              # Database connectors
│   ├── logger/                 # Logging utilities
│   ├── model/                  # Data models
│   └── repository/             # Data repositories
├── .env                        # Environment variables (gitignored)
├── .env.dist                   # Environment variables template
├── pipeline.yml                # Your pipeline config (gitignored)
├── pyproject.toml              # Project dependencies
└── README.md                   # This file
```

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal financial data aggregation only. Always:

- Keep your API keys and credentials secure
- Review the code before running
- Use at your own risk
- Comply with your financial institutions' terms of service

