# Installation Guide

This guide provides detailed installation instructions for pysystemtrade.

## System Requirements

- **Operating System**: Linux (recommended), macOS, or Windows (with WSL recommended)
- **Python**: Version 3.10 or newer
- **Memory**: Minimum 4GB RAM (8GB+ recommended for large backtests)
- **Disk Space**: 2GB minimum (more for historical data storage)

## Installation Methods

### Method 1: Standard pip Installation (Recommended for Users)

```bash
# Clone the repository
git clone https://github.com/robcarver17/pysystemtrade.git
cd pysystemtrade

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install
pip install --upgrade pip setuptools
python -m pip install .
```

### Method 2: Editable Installation (Recommended for Developers)

```bash
# Clone your fork (if contributing)
git clone https://github.com/YOUR_USERNAME/pysystemtrade.git
cd pysystemtrade

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
python -m pip install --editable '.[dev]'
```

### Method 3: Using uv (Fast, Modern Python Package Manager)

```bash
# Install uv first (see https://docs.astral.sh/uv/)
# Then:
git clone https://github.com/robcarver17/pysystemtrade.git
cd pysystemtrade

# Create environment with specific Python version
uv venv --python 3.10
source .venv/bin/activate

# Install
uv pip install .
```

## Optional Dependencies

### Arctic (Legacy Time Series Storage)

```bash
python -m pip install '.[arctic]'
```

**Note**: Arctic support is deprecated in favor of Parquet.

## Database Setup (for Production)

### MongoDB Installation

#### Ubuntu/Debian:
```bash
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```

#### macOS:
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Start MongoDB:
```bash
# Create data directory
mkdir -p ~/data/mongodb

# Start server
mongod --dbpath ~/data/mongodb
```

### Parquet Storage Setup

No additional installation required - Parquet support is included by default. Just configure the storage path in your configuration.

## Configuration

### Private Configuration Directory

Create a `private` directory in the project root for your custom configurations:

```bash
mkdir private
```

### Basic Private Config

Create `private/private_config.yaml`:

```yaml
# MongoDB connection
mongo_host: localhost
mongo_db: production

# Parquet storage
parquet_store: /path/to/your/parquet/store

# Interactive Brokers (if using)
ib_ipaddress: 127.0.0.1
ib_port: 4001
broker_account: UXXXXXX

# Email notifications (optional)
email_address: your_email@example.com
```

## Verification

### Test Basic Installation

```python
# Test Python imports
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system

# Test data access
data = csvFuturesSimData()
print(f"Available instruments: {len(data.get_instrument_list())}")

# Test system creation
system = futures_system()
positions = system.portfolio.get_notional_position("SOFR")
print(positions.tail())
```

### Test Database Connection (if using MongoDB)

```python
from sysdata.mongodb.mongo_connection import mongoDb
from sysdata.data_blob import dataBlob

# This will test MongoDB connection
data = dataBlob()
print("Database connection successful!")
```

## Troubleshooting

### Issue: ImportError for pandas/numpy

**Solution**: Ensure all dependencies are installed:
```bash
pip install pandas numpy matplotlib scipy pyyaml
```

### Issue: MongoDB connection refused

**Solution**: Check if MongoDB is running:
```bash
# Check MongoDB status
sudo systemctl status mongod  # Linux
brew services list | grep mongodb  # macOS

# Start MongoDB if needed
mongod --dbpath ~/data/mongodb
```

### Issue: Permission errors on data directories

**Solution**: Ensure proper permissions:
```bash
chmod 755 ~/data/mongodb
chmod 755 /path/to/your/parquet/store
```

### Issue: Python version mismatch

**Solution**: Check Python version and use correct interpreter:
```bash
python3 --version  # Should be 3.10+
which python3
# Use explicit path if needed
/path/to/python3.10 -m venv .venv
```

## Environment Variables

For production deployments, set these environment variables in your `~/.profile` or `~/.bashrc`:

```bash
# Project paths
export PYSYS_CODE=/home/username/pysystemtrade
export SCRIPT_PATH=$PYSYS_CODE/sysproduction/linux/scripts
export ECHO_PATH=/home/username/echos

# Data paths
export MONGO_DATA=/home/username/data/mongodb
export MONGO_BACKUP_PATH=/home/username/data/mongo_backup

# Add scripts to PATH
export PATH=$PATH:$SCRIPT_PATH
```

## Development Tools

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest syscore/tests/test_dateutils.py

# Run with verbose output
pytest -v

# Run slow tests
pytest --runslow
```

### Code Formatting

```bash
# Format all code with Black
black .

# Check format without changes
black --check .
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Next Steps

After successful installation:

1. Read the [Quick Start Guide](./index.md) for your first backtest
2. Learn about [Core Concepts](../core_concepts/architecture.md)
3. Set up your [Data Management](../data_management/data_overview.md) pipeline

---

For additional help, refer to the [GitHub repository](https://github.com/robcarver17/pysystemtrade) or [open an issue](https://github.com/robcarver17/pysystemtrade/issues).
