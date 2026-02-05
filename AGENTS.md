# AGENTS.md - Guidelines for AI Coding Agents

This file provides guidelines for AI agents working on the pysystemtrade codebase.

## Project Overview

**pysystemtrade** is a Python-based systematic futures trading framework (v1.8.2) by Robert Carver. It requires Python >=3.10 and is used for backtesting and automated trading.

## Build, Test, and Lint Commands

### Testing
```bash
# Run all tests
pytest

# Run a single test file
pytest sysdata/tests/test_config.py

# Run tests in a specific directory
pytest syscore/tests/

# Run slow tests (marked with @pytest.mark.slow)
pytest --runslow

# Run tests excluding a module
pytest --ignore=sysinit/futures/tests/test_sysinit_futures.py

# Run with verbose output
pytest -v
```

### Linting and Formatting
```bash
# Format all code with Black (REQUIRED before PR)
black .

# Format excluding virtual environment
black . --exclude '/.venv\/.+/'

# Check Black version (must be 23.11.0)
black --version
```

### Installation
```bash
# Standard install
python -m pip install .

# Editable install with dev dependencies (recommended for development)
python -m pip install --editable '.[dev]'

# Install with Arctic database support
python -m pip install '.[arctic]'
```

## Code Style Guidelines

### Formatting
- **Black** is used for code formatting (version 23.11.0)
- Line length: 88 characters
- Target Python version: 3.10+
- Run `black .` before committing

### Imports
- Use explicit imports (avoid `from module import *`)
- Standard library imports first, then third-party, then local
- Type hints should use `from typing import Union, List, Dict`

### Naming Conventions
- **Classes**: Prefer mixedCase, but single-word names use CamelCase
- **Common methods**: `get`, `calculate`, `read`, `write`
- **Dict-like objects**: Use `dict_` prefix (e.g., `dict_classOfMarketData`)
- Follow data hierarchy naming conventions (see docs/data.md)

### Type Hints
- Use type hints for all function parameters and return values
- Use `Union` for multiple possible types
- Use `arg_not_supplied` from `syscore.objects` as default sentinel instead of None

### Error Handling
- Production code should NOT throw errors unless unrecoverable
- If throwing an error, also call `log.critical()` to email the user
- Use explicit parameter passing (avoid single parameter functions unless trivial)

### Docstrings
- Verbose docstrings with all parameters are NOT required (type hints supersede)
- Remove doc tests from class methods (use unit tests instead)
- Doc tests are acceptable for standalone utility functions

## Project Structure

```
pysystemtrade/
├── syscore/           # Core utilities
├── sysdata/           # Data management
├── systems/           # Trading systems
├── sysproduction/     # Production trading
├── sysquant/          # Quantitative analysis
├── sysbrokers/        # Broker integrations (IB)
├── sysobjects/        # Data objects
├── sysexecution/      # Trade execution
├── syscontrol/        # System control/monitoring
├── sysinit/           # System initialization
├── syslogdiag/        # Logging/diagnostics
├── examples/          # Example scripts
├── docs/              # Documentation
└── tests/             # Root-level tests
```

## Testing Guidelines

- Tests are distributed across modules (e.g., `syscore/tests/`, `systems/tests/`)
- Use `@pytest.mark.slow` for long-running tests
- Prefer unit tests over doc tests for class methods
- Test coverage is sparse - add tests for new features

## Git Workflow

- **master**: Stable releases
- **develop**: Active development (branch from here)
- Branch naming: `bug-<issue#>-<description>` or `feature-<issue#>-<description>`
- Create PRs against `upstream/develop`

## Key Dependencies

- pandas==2.1.3
- numpy>=1.24.0
- PyYAML==6.0.1
- pymongo==3.11.3
- ib-insync==0.9.86 (Interactive Brokers)
- matplotlib>=3.0.0
- scipy>=1.0.0
- statsmodels==0.14.0

## CI/CD

GitHub Actions run on every PR:
- Quick tests (pytest)
- Lint check (Black 23.11.0)
- Slow tests (nightly)
- OS matrix tests (Ubuntu, macOS, Windows)

## Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```
