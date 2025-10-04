# Pipeline Configuration Examples

This folder contains example pipeline configurations for the Finance Dashboard.

## Available Examples

### 📄 pipeline-simple.yml
A simple, minimal configuration with one account per source type.

**Best for:**
- New users getting started
- Simple setups with one account per service
- Quick testing

**Includes:**
- One Bunq bank account
- One DeGiro stock account  
- Coinbase exchange
- A few Web3 wallets

### 📄 pipeline-full.yml
A comprehensive configuration showing all available options and multiple accounts.

**Best for:**
- Advanced users
- Multiple accounts per service type
- Reference documentation
- Understanding all available options

**Includes:**
- Multiple Bunq accounts (personal + business)
- Multiple DeGiro accounts
- Multiple Coinbase accounts
- Multiple Web3 wallets
- All supported wallet types and chains

## How to Use

1. **Copy an example to your project root:**
   ```bash
   cp examples/pipeline-simple.yml pipeline.yml
   # OR
   cp examples/pipeline-full.yml pipeline.yml
   ```

2. **Edit the configuration:**
   ```bash
   nano pipeline.yml
   # or use your favorite editor
   ```

3. **Set environment variables:**
   
   Make sure all environment variables referenced in your pipeline (ending with `_env`) are set in your `.env` file.
   
   Example:
   ```yaml
   # In pipeline.yml
   api_key_env: BUNQ_API_KEY
   
   # In .env
   BUNQ_API_KEY=your-actual-api-key-here
   ```

4. **Validate your configuration:**
   ```bash
   finance-dashboard --config pipeline.yml --validate-only
   ```

5. **Run the pipeline:**
   ```bash
   finance-dashboard --config pipeline.yml
   ```

## Configuration Structure

### Global Settings
```yaml
global:
  log_level: INFO
  preferred_currency: EUR
```

### Database Settings
```yaml
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
```

### Data Sources

#### Bank Accounts
```yaml
bank:
  enabled: true
  accounts:
    - name: Bunq Personal
      type: bunq
      api_key_env: BUNQ_API_KEY
      configuration_file: config/bunq_context.json
```

#### Stock Accounts
```yaml
stock:
  enabled: true
  accounts:
    - name: DeGiro
      type: degiro
      username_env: DEGIRO_USERNAME
      password_env: DEGIRO_PASSWORD
      int_account_env: DEGIRO_INT_ACCOUNT
      totp_env: DEGIRO_TOTP
```

#### Crypto Accounts
```yaml
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
    
    - name: Helium Wallet
      type: web3-solana
      wallet_address_env: HELIUM_WALLET_ADDRESS
      network: mainnet
    
    - name: Osmosis Wallet
      type: cosmos
      wallet_address_env: OSMOSIS_WALLET_ADDRESS
      network: osmosis
```

## Supported Account Types

### Bank
- **bunq**: Dutch online bank

### Stock  
- **degiro**: European online broker

### Crypto
- **coinbase**: Coinbase exchange accounts
- **web3**: EVM wallets (Ethereum, Polygon, BSC, Arbitrum, etc.)
- **web3-solana**: Solana blockchain wallets
- **cosmos**: Cosmos ecosystem wallets (Osmosis)

## Tips

### Multiple Accounts
You can configure multiple accounts per source type by adding more entries to the `accounts` list:

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

### Disabling Sources
Set `enabled: false` to skip a data source:

```yaml
bank:
  enabled: false  # Skip bank accounts
  
stock:
  enabled: true   # Collect stock data
```

### Environment Variable Naming
The `_env` suffix indicates that the value should be read from an environment variable:

```yaml
api_key_env: BUNQ_API_KEY  # Reads from env var BUNQ_API_KEY
```

Direct values (without `_env`) are used as-is:

```yaml
configuration_file: config/bunq_context.json  # Direct path
credentials_path: config/service_account.json  # Direct path
project_id: your-project-id  # Direct value
schema_id: your-schema-id  # Direct value
location: europe-west4  # Direct value
dashboard_url: https://your-dashboard.com  # Direct URL
```

## Troubleshooting

### Validation Failed
Run validation to see what's wrong:
```bash
finance-dashboard --config pipeline.yml --validate-only
```

### Missing Environment Variables
Make sure all `_env` variables are set in `.env`:
```bash
# Check if variable is set
echo $BUNQ_API_KEY

# List all environment variables
cat .env
```

### YAML Syntax Errors
Use a YAML validator or check indentation:
- Use spaces, not tabs
- Consistent indentation (2 spaces recommended)
- Proper list formatting with `-`

## Need Help?

- See `.env.dist` for all available environment variables
- Check `MIGRATION.md` for migration from old `main.py`
- Read the main `README.md` for detailed documentation
- Open an issue on GitHub for support
