# YAML-Based Backtesting System

A robust, configuration-driven backtesting framework for pysystemtrade that lets you define and run backtests using YAML files instead of hardcoded Python scripts.

## 🎯 Why YAML-Based Backtesting?

**Before (Hardcoded):**
```python
def run_my_backtest():
    rules = {
        'ewmac_64_256': create_ewmac_rule(64, 256),
        'mr_wings_4': create_mr_wings_rule(4),
    }
    config = BacktestConfig(
        instruments=['SP500', 'NASDAQ', 'US10'],
        trading_rules=rules,
        start_date="2000-01-01",
        # ... 20 more lines
    )
    # Run and plot...
```

**After (YAML Configuration):**
```yaml
name: "My Backtest"
instruments: [SP500, NASDAQ, US10]
trading_rules:
  ewmac_64_256: {type: ewmac, Lfast: 64, Lslow: 256}
  mr_wings_4: {type: mr_wings, Lfast: 4}
backtest:
  start_date: "2000-01-01"
  percentage_vol_target: 15
```

Then simply run: `python run_yaml_backtest.py configs/my_backtest.yaml`

## 📁 Directory Structure

```
my_backtests/
├── configs/                           # YAML configuration files
│   ├── trend_mr_portfolio.yaml       # Example: Trend + Mean Reversion
│   ├── multi_timeframe_trend.yaml    # Example: Multiple EWMAC timeframes
│   ├── mixed_strategies.yaml         # Example: Mixed rule types
│   └── equal_weights_test.yaml       # Example: No optimization
├── outputs/                           # Generated outputs (plots, stats)
├── backtest_framework.py              # Core backtesting framework
├── yaml_config_loader.py              # YAML parsing and loading
├── run_yaml_backtest.py               # CLI tool for running backtests
├── batch_compare.py                   # Batch comparison tool
└── YAML_GUIDE.md                      # This file
```

## 🚀 Quick Start

### 1. Run a Single Backtest

```bash
cd my_backtests
python run_yaml_backtest.py configs/trend_mr_portfolio.yaml
```

This will:
- Load the configuration
- Run the backtest
- Print performance statistics
- Display cumulative returns and drawdown plots
- Save plots to the output directory

### 2. Run Multiple Backtests

```bash
python run_yaml_backtest.py configs/trend_mr_portfolio.yaml configs/mixed_strategies.yaml
```

### 3. Run All Backtests in a Directory

```bash
python run_yaml_backtest.py configs/*.yaml
```

### 4. Compare Multiple Backtests

```bash
python batch_compare.py configs/
```

This generates:
- Comparison table of key metrics (Sharpe, returns, drawdown, etc.)
- Side-by-side performance charts
- Risk-return scatter plot

## 📝 YAML Configuration Format

### Complete Example

```yaml
# Backtest metadata
name: "My Strategy Name"
description: "Brief description of what this backtest does"

# Instruments to trade
instruments:
  - SP500
  - NASDAQ
  - US10

# Trading rules configuration
trading_rules:
  ewmac_64_256:
    type: ewmac
    Lfast: 64
    Lslow: 256
    forecast_scalar: null  # null = auto-estimate

  mr_wings_4:
    type: mr_wings
    Lfast: 4
    forecast_scalar: null

  breakout_80:
    type: breakout
    lookback: 80
    smooth: null  # null = use default (lookback/4)

# Backtest parameters
backtest:
  # Date range
  start_date: "2000-01-01"
  end_date: null  # null = use all available data

  # Capital and risk
  notional_trading_capital: 1000000
  base_currency: "USD"
  percentage_vol_target: 15

  # Forecast combination
  forecast_weight_method: "shrinkage"  # options: shrinkage, equal_weights, handcraft
  forecast_scalar_pooling: false

  # Portfolio/instrument weights
  instrument_weight_method: "shrinkage"

  # Use optimization?
  use_estimations: true  # false = equal weights everywhere

# Output settings
output:
  save_results: true
  output_dir: "outputs"
  plot_filename: "my_backtest.png"
  export_stats: true
  stats_filename: "my_backtest_stats.csv"
```

### Available Rule Types

#### 1. EWMAC (Exponentially Weighted Moving Average Crossover)

Trend-following rule that generates signals when fast MA crosses slow MA.

```yaml
ewmac_32_128:
  type: ewmac
  Lfast: 32        # Fast moving average period
  Lslow: 128       # Slow moving average period
  forecast_scalar: null
```

Common configurations:
- Fast: (8, 32), (16, 64)
- Medium: (32, 128)
- Slow: (64, 256)

#### 2. Mean Reversion Wings

Fades extreme moves by buying dips and selling rallies.

```yaml
mr_wings_4:
  type: mr_wings
  Lfast: 4         # Fast period (slow = Lfast * 4)
  forecast_scalar: null
```

#### 3. Breakout

Donchian channel-style breakout system.

```yaml
breakout_80:
  type: breakout
  lookback: 80     # Lookback period for high/low
  smooth: null     # Smoothing period (default: lookback/4)
  forecast_scalar: null
```

Common lookbacks: 20, 40, 80, 160, 320

#### 4. Carry

Buys high carry (positive roll yield), sells low carry. Only works for futures.

```yaml
carry_90:
  type: carry
  smooth_days: 90  # Smoothing period for carry signal
  forecast_scalar: null
```

#### 5. Acceleration

Measures change in trend (acceleration/deceleration of momentum).

```yaml
accel_4:
  type: accel
  Lfast: 4         # Fast period (slow = Lfast * 4)
  forecast_scalar: null
```

## 🛠️ Advanced Usage

### CLI Options

```bash
# Run without displaying plots
python run_yaml_backtest.py configs/my_backtest.yaml --no-plot

# Export statistics to CSV (overrides YAML setting)
python run_yaml_backtest.py configs/my_backtest.yaml --export-stats

# Quiet mode (less verbose output)
python run_yaml_backtest.py configs/my_backtest.yaml --quiet
```

### Batch Comparison Options

```bash
# Compare with custom output path
python batch_compare.py configs/ --output custom_comparison.png

# Export comparison table to CSV
python batch_compare.py configs/ --csv comparison_table.csv

# Run without displaying plots
python batch_compare.py configs/ --no-plot
```

### Using in Python Scripts

```python
from yaml_config_loader import load_backtest_from_yaml
from backtest_framework import BacktestRunner

# Load configuration
config, metadata, output_settings = load_backtest_from_yaml('configs/my_backtest.yaml')

# Create and run backtest
runner = BacktestRunner(config)
runner.build_system()
results = runner.run()

# Access results
print(results.stats())
runner.print_results(results)
runner.plot_results(results)

# Export statistics
runner.export_stats_to_csv(results, 'my_stats.csv')
```

## 💡 Creating New Backtests

### Method 1: Copy and Modify

1. Copy an existing YAML file from `configs/`
2. Modify instruments, rules, and parameters
3. Run it!

```bash
cp configs/trend_mr_portfolio.yaml configs/my_custom_test.yaml
# Edit my_custom_test.yaml
python run_yaml_backtest.py configs/my_custom_test.yaml
```

### Method 2: Start from Scratch

Create a new YAML file with the minimum required fields:

```yaml
name: "Minimal Backtest"
instruments: [SP500]
trading_rules:
  ewmac_64_256:
    type: ewmac
    Lfast: 64
    Lslow: 256
backtest:
  start_date: "2000-01-01"
output:
  output_dir: "outputs"
```

## 🔬 Experimental Design Tips

### 1. Parameter Sweeps

Create multiple YAML files with systematic variations:

```
configs/sweep_ewmac/
├── ewmac_8_32.yaml
├── ewmac_16_64.yaml
├── ewmac_32_128.yaml
└── ewmac_64_256.yaml
```

Then compare: `python batch_compare.py configs/sweep_ewmac/`

### 2. Instrument Sensitivity

Test how strategy performs with different instrument sets:

```yaml
# config_equities_only.yaml
instruments: [SP500, NASDAQ]

# config_bonds_only.yaml
instruments: [US10, BOBL]

# config_mixed.yaml
instruments: [SP500, US10]
```

### 3. Optimization vs. Equal Weights

Create paired configs to compare optimized vs. naive approaches:

```yaml
# optimized.yaml
backtest:
  use_estimations: true
  forecast_weight_method: "shrinkage"

# equal_weights.yaml
backtest:
  use_estimations: false
  forecast_weight_method: "equal_weights"
```

## 🎓 Understanding the Configuration System

### Configuration Inheritance

pysystemtrade uses a 3-tier configuration lookup:

1. **Your YAML config** (highest priority)
2. **Private config** (`private/private_config.yaml`)
3. **System defaults** (`sysdata/config/defaults.yaml`)

The framework **modifies** defaults rather than replacing them, ensuring all required parameters (like optimizer functions) are preserved.

### Forecast Weighting Methods

- `shrinkage`: Bayesian shrinkage toward equal weights (robust, recommended)
- `equal_weights`: Simple equal weighting (baseline)
- `handcraft`: Use fixed weights from config (advanced)

### Instrument Weighting Methods

Same options as forecast weighting, but applied at the portfolio level.

## 🐛 Troubleshooting

### Problem: "FileNotFoundError: Config file not found"

**Solution:** Check that the path to your YAML file is correct. Use tab completion or full paths.

### Problem: "KeyError: 'func'" or similar optimizer errors

**Solution:** This usually means config inheritance is broken. The framework should handle this automatically, but if you see this error, check that you're not manually creating `Config()` objects in custom code.

### Problem: No plots showing up

**Solution:**
- Make sure you're not using `--no-plot` flag
- Check that output directory exists and is writable
- Verify matplotlib backend is configured correctly

### Problem: Backtest runs but stats look wrong

**Solution:**
- Verify your instruments exist in the data directory
- Check date ranges - some instruments may have limited history
- Ensure trading rules are configured correctly (check Lfast < Lslow for EWMAC)

## 📊 Output Files

### Plots

Default location: `outputs/<plot_filename>.png`

Contains:
- Cumulative returns (gross and net)
- Drawdown chart

### Statistics CSV

Default location: `outputs/<stats_filename>.csv`

Contains metrics for:
- Portfolio (aggregate)
- Each individual instrument

Metrics include:
- Sharpe ratio
- Annual return and volatility
- Maximum drawdown
- Calmar ratio
- Sortino ratio
- Skewness

## 🔮 Next Steps

### Extending the Framework

1. **Add new rule types**: Edit `yaml_config_loader.py` and add to `RULE_CREATORS`
2. **Custom output formats**: Extend `BacktestRunner.export_stats_to_csv()`
3. **HTML reports**: Implement `BacktestComparator.generate_html_report()` (marked with TODO)
4. **Real-time monitoring**: Add logging and progress bars for long-running backtests

### Integration with Production

The YAML configs can be used to:
- Document your live trading strategies
- Version control strategy parameters
- A/B test different approaches in simulation
- Generate reports for stakeholders

## 📚 Further Reading

- [pysystemtrade Documentation](https://github.com/robcarver17/pysystemtrade)
- [Systematic Trading Book](https://www.systematicmoney.org/)
- See `docs/backtesting.md` in the main pysystemtrade repository

---

**Happy backtesting! 🚀**
