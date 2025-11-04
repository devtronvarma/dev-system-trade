# Quick Usage Guide

## Directory Structure

```
my_backtests/
├── backtest_framework.py      # Core framework (don't modify)
├── my_backtests.py             # Your configurations (modify this!)
├── BACKTEST_README.md          # Detailed framework documentation
├── RULES_REFERENCE.md          # All trading rules explained
├── notebooks/                  # Jupyter notebooks for exploration
│   ├── ewmac_mrwings_3.ipynb  # Working example notebook
│   └── introduction.ipynb      # pysystemtrade basics
├── outputs/                    # All plots and results go here (gitignored)
└── configs/                    # Optional: store config files
```

## Running Backtests

### Option 1: Run from my_backtests directory

```bash
cd my_backtests
python my_backtests.py
```

All outputs will be saved to `outputs/`

### Option 2: Create a new backtest file

```bash
cd my_backtests
cp my_backtests.py my_experiment.py
# Edit my_experiment.py
python my_experiment.py
```

### Option 3: Use Jupyter notebooks

```bash
cd my_backtests/notebooks
jupyter notebook ewmac_mrwings_3.ipynb
```

## Common Tasks

### 1. Test Different Instruments

Edit `my_backtests.py`:
```python
config = BacktestConfig(
    instruments=['CORN', 'GOLD', 'CRUDE_W'],  # Change these
    ...
)
```

### 2. Add More Trading Rules

```python
rules = {
    'ewmac_fast': create_ewmac_rule(16, 64),
    'ewmac_slow': create_ewmac_rule(64, 256),
    'breakout': create_breakout_rule(80),
    'mr_wings': create_mr_wings_rule(4),
}
```

### 3. Change Date Range

```python
config = BacktestConfig(
    start_date="2010-01-01",
    end_date="2023-12-31",
    ...
)
```

### 4. Adjust Risk Level

```python
config = BacktestConfig(
    percentage_vol_target=15,  # Lower = less risk
    ...
)
```

## Viewing Results

### Plots
All plots are saved to `outputs/` directory as PNG files.

### Statistics
Printed to console during backtest run. Key metrics:
- **sharpe**: Risk-adjusted returns (>0.5 is good)
- **ann_mean**: Annual return %
- **avg_drawdown**: Average decline from peaks

### Re-running
Outputs are gitignored, so you can re-run backtests without cluttering git history.

## Tips

1. **Start small**: Test with 2-3 instruments first
2. **Compare methods**: Run same backtest with `use_estimations=True` vs `False`
3. **Save important results**: Copy good plots from outputs/ to a permanent location
4. **Document experiments**: Add comments to your backtest functions
5. **Use notebooks**: Great for exploring data and visualizing intermediate results

## Getting Help

- **Framework basics**: See `BACKTEST_README.md`
- **Trading rules**: See `RULES_REFERENCE.md`
- **pysystemtrade**: Check the main pysystemtrade docs
- **Issues**: Check the notebooks/ directory for working examples
