# Production Trading Setup

This guide covers setting up pysystemtrade for live production trading.

## Prerequisites

Before setting up production trading:

1. **Complete backtesting**: Have a thoroughly tested strategy
2. **Paper trading**: Test with IB paper account first
3. **Data ready**: Complete historical data setup
4. **Infrastructure**: Reliable server, backup systems
5. **Risk management**: Understand position limits, overrides

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Production System                         │
├─────────────────────────────────────────────────────────────┤
│  Scheduler (cron) → Scripts → Data Updates → Backtests      │
│                                    ↓                        │
│  Order Generation → Order Stack → Broker Execution          │
│                                    ↓                        │
│  Position Updates → Reporting → Monitoring                  │
└─────────────────────────────────────────────────────────────┘
```

## Installation and Setup

### 1. Environment Setup

Create production environment:

```bash
# Create dedicated user
sudo useradd -m trading
sudo usermod -aG sudo trading
su - trading

# Clone repository
git clone https://github.com/robcarver17/pysystemtrade.git
cd pysystemtrade

# Install
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
python -m pip install .
```

### 2. Directory Structure

```
/home/trading/
├── pysystemtrade/              # Code
├── data/
│   ├── mongodb/               # MongoDB data
│   ├── parquet/               # Parquet files
│   ├── mongo_dump/            # MongoDB backups
│   ├── backups_csv/           # CSV backups
│   └── reports/               # Generated reports
├── echos/                     # Process output logs
└── logs/                      # Application logs
```

### 3. Environment Variables

Add to `~/.profile`:

```bash
# Project paths
export PYSYS_CODE=/home/trading/pysystemtrade
export SCRIPT_PATH=$PYSYS_CODE/sysproduction/linux/scripts
export ECHO_PATH=/home/trading/echos

# Data paths
export MONGO_DATA=/home/trading/data/mongodb
export MONGO_BACKUP_PATH=/home/trading/data/mongo_dump
export PARQUET_PATH=/home/trading/data/parquet

# IB Gateway path (optional)
export IB_GATEWAY_PATH=/opt/ibgateway

# Add scripts to PATH
export PATH=$PATH:$SCRIPT_PATH
```

### 4. Configuration Files

**Private Config** (`private/private_config.yaml`):
```yaml
# Database
mongo_host: localhost
mongo_db: production
parquet_store: /home/trading/data/parquet

# Interactive Brokers
ib_ipaddress: 127.0.0.1
ib_port: 4001
broker_account: UXXXXXXXX

# Trading parameters
percentage_vol_target: 25.0
notional_trading_capital: 500000
base_currency: USD

# Notifications
email_address: your_email@example.com
smtp_server: smtp.gmail.com
smtp_port: 587
smtp_username: your_email@example.com
smtp_password: your_app_password

# Paths
echo_path: /home/trading/echos
backup_path: /home/trading/data/backups_csv
```

**Control Config** (`private/private_control_config.yaml`):
```yaml
# Process configuration
process_configuration:
  run_daily_price_updates:
    run_mode: auto
    start_time: "00:01"
    end_time: "23:59"
    frequency: Daily
  
  run_systems:
    run_mode: auto
    start_time: "06:00"
    end_time: "08:00"
    frequency: Daily
  
  run_strategy_order_generator:
    run_mode: auto
    start_time: "06:30"
    end_time: "08:00"
    frequency: Daily
  
  run_stack_handler:
    run_mode: auto
    start_time: "07:00"
    end_time: "22:00"
    frequency: Daily

# Dashboard
dashboard_visible_on_lan: false
dashboard_port: 5000

# Logging
log_level: INFO
log_to_file: true
log_to_screen: false
log_to_email: true
```

## Interactive Brokers Setup

### 1. Install IB Gateway

Download and install IB Gateway from Interactive Brokers website.

### 2. Configure Gateway

Settings:
- **Socket port**: 4001
- **Allow connections from**: 127.0.0.1 (or your server IP)
- **Read-only API**: OFF (for trading)
- **Create API message log**: Optional

### 3. Auto-Start Gateway (Optional)

Use IBC (IB Controller) for automatic login:

```bash
# Download ibcAlpha from GitHub
# Configure config.ini with credentials
# Create startup script
```

### 4. Test Connection

```python
from sysbrokers.IB.ib_connection import connectionIB

conn = connectionIB(
    client_id=1,
    ib_ipaddress="127.0.0.1",
    ib_port=4001,
    account="UXXXXXXXX"
)

print(f"Connected: {conn}")
conn.close_connection()
```

## Database Setup

### MongoDB

```bash
# Install MongoDB (see installation guide)
# Create data directory
mkdir -p /home/trading/data/mongodb

# Start MongoDB
mongod --dbpath /home/trading/data/mongodb --fork --logpath /var/log/mongod.log

# Verify
mongo --eval "db.version()"
```

### Initialize Data

```python
# 1. Instrument configuration
from sysinit.futures.repocsv_spread_costs import init_spread_costs
init_spread_costs()

# 2. FX data
from sysinit.futures.repocsv_spotfx_prices import init_spotfx_prices
init_spotfx_prices()

# 3. Futures contract prices (seed from IB)
from sysinit.futures.seed_price_data_from_IB import seed_price_data_from_IB
# Seed major instruments
for instrument in ['SOFR', 'US10', 'SP500_micro', 'NASDAQ_micro']:
    seed_price_data_from_IB(instrument)

# 4. Roll calendars
from sysinit.futures.rollcalendars_from_db_prices_to_csv import build_and_write_roll_calendar
for instrument in ['SOFR', 'US10', 'SP500_micro', 'NASDAQ_micro']:
    build_and_write_roll_calendar(instrument)

# 5. Multiple and adjusted prices
from sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db import process_multiple_prices_single_instrument
from sysinit.futures.adjustedprices_from_db_multiple_to_db import process_adjusted_prices_single_instrument

for instrument in ['SOFR', 'US10', 'SP500_micro', 'NASDAQ_micro']:
    process_multiple_prices_single_instrument(instrument)
    process_adjusted_prices_single_instrument(instrument)
```

## Scheduling

### Cron Setup

Edit crontab:
```bash
crontab -e
```

Add entries:
```cron
# Environment
PATH=/home/trading/.venv/bin:/usr/local/bin:/usr/bin:/bin
PYSYS_CODE=/home/trading/pysystemtrade
SCRIPT_PATH=$PYSYS_CODE/sysproduction/linux/scripts

# Daily price updates (1 AM)
0 1 * * * $SCRIPT_PATH/run_daily_price_updates >> /home/trading/echos/price_updates.log 2>&1

# Update FX prices (6 AM)
0 6 * * * $SCRIPT_PATH/update_fx_prices >> /home/trading/echos/fx_updates.log 2>&1

# Run systems and generate orders (6:30 AM)
30 6 * * * $SCRIPT_PATH/run_systems >> /home/trading/echos/run_systems.log 2>&1

# Execute orders (7 AM - 10 PM)
0 7-22 * * * $SCRIPT_PATH/run_stack_handler >> /home/trading/echos/stack_handler.log 2>&1

# Daily reports (8 AM)
0 8 * * * $SCRIPT_PATH/run_reports >> /home/trading/echos/reports.log 2>&1

# Backups (2 AM)
0 2 * * * $SCRIPT_PATH/run_backups >> /home/trading/echos/backups.log 2>&1

# Clean old logs (Sunday 3 AM)
0 3 * * 0 $SCRIPT_PATH/run_cleaners >> /home/trading/echos/cleaners.log 2>&1
```

## Daily Workflow

### Automated Process

1. **Price Updates** (1:00 AM)
   - Update individual contract prices
   - Update sampled contracts
   - Download from Interactive Brokers

2. **FX Updates** (6:00 AM)
   - Update spot FX rates
   - Required for position sizing

3. **System Run** (6:30 AM)
   - Run backtest with latest data
   - Calculate optimal positions
   - Generate desired trades

4. **Order Generation** (6:35 AM)
   - Create instrument orders
   - Apply position limits and overrides
   - Spawn contract orders

5. **Order Execution** (7:00 AM - 10:00 PM)
   - Submit broker orders
   - Monitor fills
   - Update positions

6. **Reporting** (8:00 AM)
   - Generate daily reports
   - Send email summaries
   - Update dashboard

### Manual Interventions

**Check Prices**:
```bash
. interactive_manual_check_historical_prices
```

**View/Modify Positions**:
```bash
. interactive_controls
# Select: Positions and Orders
```

**Emergency Stop**:
```bash
. interactive_order_stack
# Cancel all orders, set overrides
```

## Monitoring

### Dashboard

Start web dashboard:
```bash
cd $PYSYS_CODE/dashboard
python app.py
```

Access at `http://localhost:5000`

### System Monitor

Alternative text-based monitor:
```bash
cd $PYSYS_CODE/syscontrol
python monitor.py
```

### Log Files

Check logs regularly:
```bash
# Echo files (process output)
tail -f /home/trading/echos/*.log

# Application logs
tail -f /var/log/pysystemtrade/*.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log
```

### Email Alerts

Configure email for critical alerts:
- Process failures
- Order rejections
- Large P&L moves
- System errors

## Risk Management

### Position Limits

Set in interactive controls:
```bash
. interactive_controls
# Select: Position Limits
# Set max/min positions per instrument
```

### Trade Limits

Control trading frequency:
```bash
. interactive_controls
# Select: Trade Limits
# Set max trades per day/hour
```

### Overrides

Emergency position modifications:
```bash
. interactive_controls
# Select: Trade Control (Override)
# Options:
#   - Reduce only (close positions)
#   - No trading (stop new trades)
#   - Custom multiplier
```

### Capital Controls

Monitor and update capital:
```bash
. interactive_update_capital_manual
# View current capital
# Update strategy allocations
# Handle withdrawals/deposits
```

## Backup and Recovery

### Automated Backups

Daily backup (configured in crontab):
```bash
# MongoDB dump
mongodump --db production --out $MONGO_BACKUP_PATH/$(date +%Y%m%d)

# CSV export
. run_backups

# Parquet backup (if using)
. backup_parquet_data_to_remote
```

### Recovery Procedures

**Database Corruption**:
```bash
# Stop production
# Restore from latest backup
mongorestore --db production $MONGO_BACKUP_PATH/latest/production

# Verify data integrity
. interactive_diagnostics
```

**System Failure**:
1. Stop all processes
2. Check log files for errors
3. Restart IB Gateway if needed
4. Restart MongoDB if needed
5. Resume from last known good state
6. Manually verify positions match broker

## Troubleshooting

### Issue: Orders Not Executing

**Check**:
- IB Gateway connected?
- Market hours?
- Order limits reached?
- Position limits blocking?

**Debug**:
```bash
. interactive_order_stack
# Check order status
# Look for errors
```

### Issue: Data Stale

**Check**:
- Price update process running?
- IB data feed active?
- MongoDB running?

**Fix**:
```bash
# Manually update
. run_daily_price_updates

# Check last update times
. interactive_diagnostics
# Select: View Prices
```

### Issue: System Crashes

**Check logs**:
```bash
tail -100 /home/trading/echos/run_systems.log
grep ERROR /var/log/pysystemtrade/*.log
```

**Common causes**:
- Out of memory
- Database connection lost
- IB connection timeout
- Data corruption

## Security Considerations

1. **Firewall**: Only open necessary ports (IB: 4001, MongoDB: 27017, Dashboard: 5000)
2. **SSH**: Use key-based authentication, disable password login
3. **IB Gateway**: Use paper account for testing, whitelist IPs
4. **Secrets**: Store passwords in private_config.yaml (not in git)
5. **Backups**: Encrypt backup files, store offsite

## Best Practices

1. **Test Thoroughly**: Paper trade for months before live
2. **Start Small**: Trade reduced size initially
3. **Monitor Closely**: Check systems multiple times daily
4. **Have Backups**: Redundant data, backup server ready
5. **Document Procedures**: Write down all manual steps
6. **Regular Reviews**: Weekly performance and risk review
7. **Stay Updated**: Keep code and dependencies current

## Next Steps

- Learn about [Production Workflow](./production_workflow.md)
- Understand [Order Management](./order_management.md)
- Set up [Monitoring](./monitoring.md)
- Read about [Strategy Changes](../production_strategy_changes.md)
