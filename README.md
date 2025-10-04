# Finance Dashboard 📊

A comprehensive personal finance data aggregation tool that automatically collects and centralizes financial data from multiple sources into Google BigQuery for analysis and visualization.

## 🌟 Features

- **Multi-Source Data Collection**: Supports banks (Bunq), brokers (DeGiro), crypto exchanges (Coinbase), and Web3 wallets
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

4. **Set up Google Cloud BigQuery:**

   - Create a Google Cloud Project
   - Enable the BigQuery API
   - Create a dataset for storing financial data
   - Download service account credentials to `config/service_account.json`

5. **Run the application:**

   ```bash
   python main.py
   ```

## 💻 Usage

### Manual Execution

Run the dashboard manually to collect current financial data:

```bash
python main.py
```

### Automated Scheduling

For daily automated data collection, set up a cron job:

```bash
crontab -e
```

Add this line to run daily at midnight:

```bash
0 0 * * * cd /path/to/finance-dashboard && python main.py
```

### Monitoring

- **Logs**: Check daily log files in the `logs/` directory
- **Telegram**: Receive error notifications via Telegram (if configured)
- **BigQuery**: Monitor data in your BigQuery dataset

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for personal financial data aggregation only. Always:

- Keep your API keys and credentials secure
- Review the code before running
- Use at your own risk
- Comply with your financial institutions' terms of service

