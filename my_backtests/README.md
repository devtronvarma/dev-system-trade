# My Backtests

This directory contains custom backtesting configurations and analysis.

## Directory Structure

```
my_backtests/
├── backtest_framework.py   # Core backtesting framework
├── my_backtests.py          # Your custom backtest configurations
├── BACKTEST_README.md       # Framework usage guide
├── RULES_REFERENCE.md       # Complete trading rules reference
├── notebooks/               # Jupyter notebooks for exploration
│   ├── introduction.ipynb
│   └── ewmac_mrwings_3.ipynb
├── outputs/                 # Generated plots and results (gitignored)
└── configs/                 # Optional: store backtest configs as JSON/YAML
```

## Quick Start

1. **Run a backtest:**
   ```bash
   cd my_backtests
   python my_backtests.py
   ```

2. **View results:**
   - Plots saved to `outputs/`
   - Statistics printed to console

3. **Create new backtests:**
   - Edit `my_backtests.py` and add new functions
   - Or create separate files that import from `backtest_framework`

## Available Documentation

- **BACKTEST_README.md** - How to use the framework
- **RULES_REFERENCE.md** - All available trading rules and configurations

## Examples

See `my_backtests.py` for examples of:
- Trend + mean reversion portfolios
- Multi-timeframe strategies
- Mixed strategy types
- Custom date ranges

## Outputs

All plots and results are saved to `outputs/` directory. This directory is gitignored to keep your repository clean.
