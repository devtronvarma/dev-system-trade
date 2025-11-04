# Backtesting Framework - Quick Start Guide

This framework makes it easy to run systematic trading backtests with different configurations.

## Files

- **`backtest_framework.py`** - Core framework (don't modify unless you know what you're doing)
- **`my_backtests.py`** - Your custom backtest configurations (modify this!)

## Quick Start

### 1. Run a Pre-configured Backtest

```bash
python my_backtests.py
```

This will run the default trend + mean reversion backtest and save results.

### 2. Modify Existing Backtests

Edit `my_backtests.py` and uncomment different backtest functions:

```python
if __name__ == "__main__":
    # Run the trend + mean reversion portfolio
    runner1, results1 = run_trend_mr_portfolio()

    # Uncomment to run additional backtests:
    runner2, results2 = run_multi_timeframe_trend()
    runner3, results3 = run_equal_weights_backtest()
```

### 3. Create Your Own Backtest

Add a new function to `my_backtests.py`:

```python
def run_my_custom_backtest():
    """
    My custom backtest description
    """
    # Define rules
    rules = {
        'ewmac_16_64': create_ewmac_rule(16, 64),
        'ewmac_32_128': create_ewmac_rule(32, 128),
    }

    # Configure backtest
    config = BacktestConfig(
        instruments=['SP500', 'EUROSTX', 'US10'],
        trading_rules=rules,
        start_date="2005-01-01",
        end_date="2023-12-31",
        percentage_vol_target=18,
        notional_trading_capital=750_000,
        base_currency="USD",
    )

    # Run it
    runner = BacktestRunner(config)
    runner.build_system()
    results = runner.run()
    runner.print_results(results)
    runner.plot_results(results, save_path='my_custom_backtest.png')

    return runner, results
```

## Configuration Options

### BacktestConfig Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `instruments` | List of instrument codes | `['SP500', 'US10']` |
| `trading_rules` | Dict of rule_name: TradingRule | `{'ewmac': create_ewmac_rule(32, 128)}` |
| `start_date` | Backtest start (YYYY-MM-DD) | `"2000-01-01"` |
| `end_date` | Backtest end or None for all data | `"2023-12-31"` or `None` |
| `percentage_vol_target` | Annual volatility target (%) | `15` (conservative) to `25` (aggressive) |
| `notional_trading_capital` | Starting capital | `1_000_000` |
| `base_currency` | Currency code | `"USD"`, `"GBP"`, etc. |
| `forecast_scalar_pooling` | Pool scalars across instruments? | `False` (default) or `True` |
| `forecast_weight_method` | How to weight rules | `"shrinkage"`, `"equal_weights"`, `"bootstrap"` |
| `instrument_weight_method` | How to weight instruments | `"shrinkage"`, `"equal_weights"` |
| `use_estimations` | Use optimization or equal weights? | `True` (default) or `False` |

## Available Trading Rules

### EWMAC (Trend Following)

```python
create_ewmac_rule(Lfast, Lslow)
```

**Common Configurations:**
- **Fast**: `(8, 32)` - Catches short-term trends
- **Medium**: `(16, 64)` or `(32, 128)` - Balanced
- **Slow**: `(64, 256)` - Long-term trends only

### MR Wings (Mean Reversion)

```python
create_mr_wings_rule(Lfast)
```

**Common Configurations:**
- **Aggressive**: `Lfast=2` - Reacts quickly to extremes
- **Standard**: `Lfast=4` - Balanced (default)
- **Conservative**: `Lfast=8` - Only trades major extremes

## Common Use Cases

### 1. Test Multiple Timeframes

```python
rules = {
    'ewmac_fast': create_ewmac_rule(16, 64),
    'ewmac_medium': create_ewmac_rule(32, 128),
    'ewmac_slow': create_ewmac_rule(64, 256),
}
```

### 2. Different Instruments, Different Rules

To apply specific rules to specific instruments, you need to modify the framework or use filtering in post-processing. For now, all rules apply to all instruments with automatic weighting.

### 3. Compare Estimation Methods

Run the same backtest with different estimation settings:

```python
# With optimization
config1 = BacktestConfig(..., use_estimations=True)

# With equal weights
config2 = BacktestConfig(..., use_estimations=False)
```

### 4. Test Specific Market Regimes

```python
# Bull market
config = BacktestConfig(..., start_date="2010-01-01", end_date="2019-12-31")

# Including COVID
config = BacktestConfig(..., start_date="2019-01-01", end_date="2023-12-31")
```

## Output

Each backtest produces:

1. **Console Output**: Detailed statistics including Sharpe ratio, returns, drawdowns
2. **Plot**: Cumulative returns and drawdown chart (saved as PNG)
3. **Returns Object**: Can be used for further analysis

## Understanding the Results

### Key Metrics to Watch

- **Sharpe Ratio**: Risk-adjusted returns. >0.5 is decent, >1.0 is excellent
- **Annual Return (ann_mean)**: Your average yearly return
- **Max Drawdown**: Worst peak-to-trough decline
- **Hit Rate**: Percentage of profitable days
- **p-value**: Statistical significance (<0.05 means results likely not random)

### Gross vs Net Returns

- **Gross**: Returns before trading costs
- **Net**: Returns after trading costs (more realistic)

The difference shows your transaction costs impact.

## Tips

1. **Start Simple**: Begin with 2-3 instruments and 2 rules
2. **Equalize Data**: Use `start_date` to ensure all instruments have data
3. **Watch Correlation**: Highly correlated instruments (like SP500 & NASDAQ) may get similar weights
4. **Vol Target**: Lower = more conservative, higher = more aggressive
5. **Compare Methods**: Try both `use_estimations=True` and `False` to see the difference

## Next Steps

- Experiment with different rule parameters
- Try different instrument combinations
- Test various market regimes (bull, bear, crisis)
- Compare estimation methods (shrinkage vs equal weights)
- Add custom trading rules (see `backtest_framework.py` for examples)

## How the Configuration System Works

### Important: Config Inheritance

The framework uses pysystemtrade's default configuration system, which loads comprehensive settings from `sysdata/config/defaults.yaml`. **This is critical to understand**:

1. **Default values are automatically loaded**: When you create a `Config()` object, it includes all optimizer settings, estimators, and parameters from `defaults.yaml`

2. **We modify, not replace**: The framework **modifies** existing config dictionaries rather than replacing them. This preserves all the required parameters like:
   - `func`: The optimizer function (e.g., `genericOptimiser`)
   - `ceiling_cost_SR`: Cost constraints
   - Correlation, mean, and volatility estimators

3. **What gets customized**: When you set:
   ```python
   forecast_weight_method="shrinkage"
   instrument_weight_method="shrinkage"
   ```
   The framework only overrides the `method` parameter while keeping all other defaults intact.

### Why This Matters

**❌ Wrong approach** (will cause `KeyError: 'func'`):
```python
my_config.instrument_weight_estimate = dict(
    method="shrinkage",
    date_method="in_sample"
)  # This REPLACES the entire dict, losing 'func' and other params!
```

**✓ Correct approach** (used by this framework):
```python
my_config.instrument_weight_estimate["method"] = "shrinkage"
# This MODIFIES the existing dict, keeping 'func' and all defaults
```

### Optimization Methods

When `use_estimations=True`, the framework uses:

- **`method="shrinkage"`**: Sophisticated optimization balancing historical returns with risk
- **`method="handcraft"`**: Uses predefined rules with some optimization
- **`date_method="expanding"`**: Uses all historical data up to each point (standard for backtesting)

When `use_estimations=False`:
- Uses equal weights for both rules and instruments
- Much faster, good for quick tests
- Simpler to understand results

## Troubleshooting

**"KeyError: 'func'"**: This means the config inheritance was broken. Make sure you're using a recent version of the framework that properly modifies config dicts rather than replacing them.

**"Instrument not found"**: Check spelling and ensure data exists in CSV files

**"All NaN values"**: Rule might need volatility data - see MR Wings example for proper data configuration

**"Zero positions"**: Instrument might be getting zero weight due to short history or high correlation

**"Different results each run"**: Normal if using estimation - uses expanding window that updates with data

**"No objects to concatenate"**: Can occur if `date_method` is incompatible with data availability. The framework uses `"expanding"` by default which should work in most cases.