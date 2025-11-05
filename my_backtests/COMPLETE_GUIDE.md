# Complete YAML Backtesting System Guide

## 🎯 Overview

You now have a **production-grade, configuration-driven backtesting system** that transforms how you test trading strategies. Instead of hardcoding backtests in Python, you define them in YAML files and run them with simple commands.

### Key Benefits

✅ **Declarative Configuration** - Define strategies in YAML, not code
✅ **Rapid Experimentation** - Test new ideas in minutes, not hours
✅ **Batch Processing** - Run and compare multiple strategies simultaneously
✅ **Professional Reports** - Generate QuantStats HTML reports with one flag
✅ **Version Control Friendly** - Track strategy evolution through git
✅ **Reproducible** - Same config always produces same results

---

## 📁 System Architecture

```
my_backtests/
├── Core Framework
│   ├── backtest_framework.py      # Backtesting engine
│   ├── yaml_config_loader.py      # YAML→Config converter
│   ├── run_yaml_backtest.py       # Single/batch execution CLI
│   └── batch_compare.py           # Multi-strategy comparison
│
├── Configuration
│   └── configs/                   # Your YAML strategy definitions
│       ├── trend_mr_portfolio.yaml
│       ├── multi_timeframe_trend.yaml
│       ├── mixed_strategies.yaml
│       ├── equal_weights_test.yaml
│       └── simple_test.yaml
│
├── Outputs
│   ├── outputs/                   # Plots and CSV exports
│   └── outputs/reports/           # QuantStats HTML reports
│
└── Documentation
    ├── YAML_GUIDE.md             # YAML configuration reference
    ├── QUANTSTATS_GUIDE.md       # QuantStats integration
    └── COMPLETE_GUIDE.md         # This file
```

---

## 🚀 Quick Start Examples

### 1. Run Your First Backtest

```bash
cd my_backtests
python run_yaml_backtest.py configs/simple_test.yaml
```

**What happens:**
- Loads config from YAML
- Runs backtest on SP500 with EWMAC rule
- Prints performance statistics
- Shows cumulative returns and drawdown plots
- Saves plot to `outputs/simple_test.png`

### 2. Generate a Professional Report

```bash
python run_yaml_backtest.py configs/trend_mr_portfolio.yaml --html
```

**What you get:**
- Everything from #1, plus...
- Comprehensive QuantStats HTML report
- Open `outputs/trend_mr_portfolio_quantstats.html` in your browser

### 3. Compare Multiple Strategies

```bash
python batch_compare.py configs/
```

**What happens:**
- Runs ALL configs in the configs/ directory
- Generates comparison table (Sharpe, returns, drawdown, etc.)
- Creates side-by-side performance charts
- Plots risk-return scatter
- Saves comparison to `outputs/backtest_comparison.png`

### 4. Full Analysis Suite

```bash
python batch_compare.py configs/ --html --csv comparison.csv
```

**What you get:**
- Comparison table exported to CSV
- Comparison plots saved
- Individual QuantStats reports for EACH strategy
- Professional reports you can share with stakeholders

---

## 📝 Creating New Strategies

### Method 1: Copy and Modify (Fastest)

```bash
cp configs/trend_mr_portfolio.yaml configs/my_strategy.yaml
# Edit my_strategy.yaml
python run_yaml_backtest.py configs/my_strategy.yaml --html
```

### Method 2: Template (Minimal)

Create `configs/my_strategy.yaml`:

```yaml
name: "My New Strategy"
description: "Testing a new idea"

instruments:
  - SP500
  - US10

trading_rules:
  ewmac_32_128:
    type: ewmac
    Lfast: 32
    Lslow: 128

backtest:
  start_date: "2010-01-01"
  percentage_vol_target: 20

output:
  output_dir: "outputs"
  plot_filename: "my_strategy.png"
```

Then run:
```bash
python run_yaml_backtest.py configs/my_strategy.yaml --html
```

---

## 🔬 Common Workflows

### Workflow 1: Parameter Optimization

Test different EWMAC parameters:

```bash
# Create configs/sweep/
mkdir -p configs/sweep

# Create variations
cat > configs/sweep/ewmac_8_32.yaml << EOF
name: "EWMAC 8-32"
instruments: [SP500]
trading_rules:
  ewmac: {type: ewmac, Lfast: 8, Lslow: 32}
backtest: {start_date: "2010-01-01"}
output: {output_dir: "outputs", plot_filename: "ewmac_8_32.png"}
EOF

# Repeat for 16_64, 32_128, 64_256...

# Compare all
python batch_compare.py configs/sweep/ --html --csv sweep_results.csv
```

### Workflow 2: Instrument Sensitivity

Test how strategy performs on different assets:

```yaml
# configs/equities_only.yaml
instruments: [SP500, NASDAQ]

# configs/bonds_only.yaml
instruments: [US10, BOBL]

# configs/balanced.yaml
instruments: [SP500, US10]
```

```bash
python batch_compare.py configs/*_only.yaml configs/balanced.yaml --html
```

### Workflow 3: Strategy Combinations

Test different rule combinations:

```yaml
# configs/trend_only.yaml
trading_rules:
  ewmac_64_256: {type: ewmac, Lfast: 64, Lslow: 256}

# configs/mr_only.yaml
trading_rules:
  mr_wings_4: {type: mr_wings, Lfast: 4}

# configs/combined.yaml
trading_rules:
  ewmac_64_256: {type: ewmac, Lfast: 64, Lslow: 256}
  mr_wings_4: {type: mr_wings, Lfast: 4}
```

```bash
python batch_compare.py configs/trend_only.yaml configs/mr_only.yaml configs/combined.yaml --html
```

### Workflow 4: Optimization vs. Naive

Compare optimized weights vs. equal weights:

```yaml
# configs/optimized.yaml
backtest:
  use_estimations: true
  forecast_weight_method: "shrinkage"
  instrument_weight_method: "shrinkage"

# configs/equal_weights.yaml
backtest:
  use_estimations: false
  forecast_weight_method: "equal_weights"
  instrument_weight_method: "equal_weights"
```

---

## 🎨 Available Trading Rules

### EWMAC (Trend Following)
```yaml
ewmac_64_256:
  type: ewmac
  Lfast: 64      # Fast MA period
  Lslow: 256     # Slow MA period
```
**Common:** (8,32), (16,64), (32,128), (64,256)

### Mean Reversion Wings
```yaml
mr_wings_4:
  type: mr_wings
  Lfast: 4       # Fast period (slow = Lfast * 4)
```
**Common:** Lfast = 2, 4, 8

### Breakout
```yaml
breakout_80:
  type: breakout
  lookback: 80   # Lookback for high/low
  smooth: null   # Smoothing (default: lookback/4)
```
**Common:** 20, 40, 80, 160, 320

### Carry (Futures only)
```yaml
carry_90:
  type: carry
  smooth_days: 90  # Smoothing period
```

### Acceleration
```yaml
accel_4:
  type: accel
  Lfast: 4       # Fast period
```

---

## ⚙️ Configuration Options

### Backtest Parameters

```yaml
backtest:
  # Date range
  start_date: "2000-01-01"
  end_date: null  # null = use all data

  # Capital & Risk
  notional_trading_capital: 1000000
  base_currency: "USD"
  percentage_vol_target: 15

  # Forecast combination
  forecast_weight_method: "shrinkage"  # shrinkage|equal_weights|handcraft
  forecast_scalar_pooling: false       # Pool scalars across instruments?

  # Portfolio weights
  instrument_weight_method: "shrinkage"

  # Optimization
  use_estimations: true  # false = use equal weights everywhere
```

### Output Settings

```yaml
output:
  save_results: true
  output_dir: "outputs"
  plot_filename: "my_backtest.png"
  export_stats: true
  stats_filename: "my_backtest_stats.csv"
```

---

## 🛠️ Command Reference

### run_yaml_backtest.py

```bash
# Basic usage
python run_yaml_backtest.py configs/my_backtest.yaml

# With options
python run_yaml_backtest.py configs/my_backtest.yaml \
  --no-plot          # Don't show plots interactively
  --export-stats     # Force CSV export
  --html             # Generate QuantStats report
  --quiet            # Less verbose output

# Multiple backtests
python run_yaml_backtest.py configs/*.yaml --no-plot --html

# Wildcards
python run_yaml_backtest.py configs/ewmac_*.yaml
```

### batch_compare.py

```bash
# Basic comparison
python batch_compare.py configs/

# With options
python batch_compare.py configs/ \
  --output comparison.png    # Custom plot path
  --csv results.csv          # Export comparison table
  --html                     # Generate individual reports
  --html-dir custom_reports/ # Custom report directory
  --no-plot                  # Don't show plots
  --quiet                    # Less verbose

# Specific configs
python batch_compare.py configs/strategy1.yaml configs/strategy2.yaml --html
```

---

## 📊 Understanding Outputs

### Console Output

```
======================================================================
BACKTEST CONFIGURATION
======================================================================
Instruments: SP500, NASDAQ, US10
Trading Rules: ewmac_64_256, mr_wings_4
Period: 2000-01-01 to latest
Vol Target: 15%
Capital: $1,000,000 USD

======================================================================
PORTFOLIO PERFORMANCE (NET - after costs)
======================================================================
                           min  max   mean    median    std     sharpe  ...
```

### Plot Output

- **Top chart**: Cumulative returns (gross & net)
- **Bottom chart**: Drawdown over time

### CSV Stats Export

Rows = Strategies (Portfolio + each instrument)
Columns = Metrics (sharpe, ann_mean, ann_std, max_drawdown, calmar, etc.)

### QuantStats HTML Reports

Full tearsheet with:
- Returns analysis (cumulative, distribution, monthly heatmap)
- Risk metrics (volatility, drawdown, recovery)
- Performance stats (win rate, best/worst months)
- Visualizations (rolling Sharpe, drawdown periods)
- Benchmark comparison (if provided)

---

## 🎓 Best Practices

### 1. Version Control Your Configs

```bash
git add configs/my_new_strategy.yaml
git commit -m "Add momentum-based strategy"
```

YAML files are small and diffable - perfect for git!

### 2. Use Descriptive Names

```yaml
# Good
name: "EWMAC 64-256 + MR Wings on US Equities"

# Less helpful
name: "Test 1"
```

### 3. Document Your Rationale

```yaml
description: >
  Testing whether mean reversion adds value to trend-following
  in the current low-volatility environment. Using shorter
  lookbacks to adapt faster to regime changes.
```

### 4. Always Use --html for Final Analysis

```bash
# Quick test
python run_yaml_backtest.py configs/test.yaml

# Final analysis
python run_yaml_backtest.py configs/my_strategy.yaml --html --export-stats
```

### 5. Organize Configs by Theme

```
configs/
├── baseline/           # Reference strategies
├── trend/              # Trend-following variations
├── mean_reversion/     # MR strategies
├── mixed/              # Combined approaches
└── experiments/        # Active testing
```

### 6. Compare Against Baselines

Always include a baseline strategy in comparisons:

```bash
python batch_compare.py \
  configs/baseline/equal_weights.yaml \
  configs/experiments/my_new_idea.yaml \
  --html
```

---

## 🐛 Troubleshooting

### Problem: Config file not found

```bash
# Use absolute or relative paths
python run_yaml_backtest.py ./configs/my_backtest.yaml

# Or change directory first
cd my_backtests
python run_yaml_backtest.py configs/my_backtest.yaml
```

### Problem: Instrument not found

**Check available instruments:**
```bash
ls data/futures/adjusted_prices_csv/
```

**Fix:** Use exact instrument codes from your data directory.

### Problem: No data for date range

```
Error: No data available for SP500 before 2005-01-01
```

**Fix:** Adjust `start_date` in YAML to match available data.

### Problem: Returns look wrong

**Check:**
1. Instrument codes are correct
2. Date range has sufficient data (minimum 1 year recommended)
3. Trading rules are properly configured (Lfast < Lslow for EWMAC)

---

## 🚀 Next Steps

### 1. Test the System

```bash
cd my_backtests
python run_yaml_backtest.py configs/simple_test.yaml --html
```

### 2. Create Your First Strategy

```bash
cp configs/trend_mr_portfolio.yaml configs/my_first_strategy.yaml
# Edit the file
python run_yaml_backtest.py configs/my_first_strategy.yaml --html
```

### 3. Compare Strategies

```bash
python batch_compare.py configs/simple_test.yaml configs/my_first_strategy.yaml --html
```

### 4. Explore the Reports

```bash
# macOS
open outputs/my_first_strategy_quantstats.html

# Linux
xdg-open outputs/my_first_strategy_quantstats.html
```

---

## 📚 Additional Resources

- **YAML_GUIDE.md** - Complete YAML configuration reference
- **QUANTSTATS_GUIDE.md** - QuantStats integration details
- **backtest_framework.py** - Core framework source (well documented)
- **configs/** - Example configurations to learn from

---

## 💡 Pro Tips

1. **Quick iterations**: Use `--no-plot --quiet` for fast testing
2. **Batch everything**: Run batch_compare.py weekly to track all strategies
3. **Archive reports**: HTML files are self-contained; save them with configs
4. **Use benchmarks**: Compare against SPY/bonds in QuantStats reports
5. **Parameter sweeps**: Create directories of configs with systematic variations

---

**You're ready to build robust backtesting pipelines! 🎉**

Questions? Check the other guides or review the example configs in `configs/`.
