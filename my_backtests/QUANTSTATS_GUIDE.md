# QuantStats Integration Guide

QuantStats has been integrated into your YAML-based backtesting system! This gives you professional-quality HTML reports with minimal effort.

## 🎨 What QuantStats Provides

QuantStats generates beautiful, comprehensive HTML reports that include:

- **Returns Analysis**: Cumulative returns, monthly returns heatmap, distribution
- **Risk Metrics**: Volatility, Sharpe ratio, Sortino ratio, max drawdown
- **Performance Stats**: Win rate, best/worst months, recovery periods
- **Visualizations**: Equity curve, drawdown periods, rolling statistics
- **Comparisons**: Optional benchmark comparison (e.g., vs. SPY)

## 🚀 Usage

### Single Backtest with HTML Report

```bash
cd my_backtests
python run_yaml_backtest.py configs/trend_mr_portfolio.yaml --html
```

This generates:
- Standard plots (cumulative returns + drawdown)
- **NEW:** QuantStats HTML report in `outputs/trend_mr_portfolio_quantstats.html`

### Batch Comparison with HTML Reports

```bash
python batch_compare.py configs/ --html
```

This generates:
- Comparison table and plots
- **NEW:** Individual QuantStats reports for each backtest in `outputs/reports/`

### Custom HTML Report Directory

```bash
python batch_compare.py configs/ --html --html-dir custom_reports/
```

## 📊 Viewing Reports

After generation, open the HTML files in your browser:

```bash
# macOS
open outputs/trend_mr_portfolio_quantstats.html

# Linux
xdg-open outputs/trend_mr_portfolio_quantstats.html

# Windows
start outputs/trend_mr_portfolio_quantstats.html
```

Or simply double-click the HTML file in your file browser.

## 💻 Programmatic Usage

### Basic Report Generation

```python
from yaml_config_loader import load_backtest_from_yaml
from backtest_framework import BacktestRunner

# Load and run backtest
config, metadata, _ = load_backtest_from_yaml('configs/my_backtest.yaml')
runner = BacktestRunner(config)
runner.build_system()
results = runner.run()

# Generate QuantStats report
runner.generate_quantstats_report(
    results,
    output_path='outputs/my_report.html',
    title='My Custom Strategy'
)
```

### With Benchmark Comparison

```python
import pandas as pd
import quantstats as qs

# Download benchmark data (e.g., S&P 500)
benchmark = qs.utils.download_returns('SPY')

# Generate report with benchmark
runner.generate_quantstats_report(
    results,
    output_path='outputs/my_report_vs_spy.html',
    benchmark=benchmark,
    title='My Strategy vs. S&P 500'
)
```

### Jupyter Notebook Integration

```python
# In a Jupyter notebook, display interactive tearsheet
runner.generate_quantstats_tearsheet(results)

# Or with benchmark
runner.generate_quantstats_tearsheet(results, benchmark=benchmark)
```

## 🎓 Understanding the Data Format

QuantStats requires **period returns** (not cumulative). The framework automatically converts pysystemtrade's cumulative returns to the correct format:

```python
# This happens automatically in BacktestRunner._get_returns_series()
curve = portfolio_returns.net.percent.curve()  # Cumulative returns
returns = curve.pct_change().fillna(0)  # Period returns for QuantStats
```

## 📈 Advanced: Custom Metrics

You can extend the reports by accessing the returns series directly:

```python
# Get returns in QuantStats format
returns = runner._get_returns_series(results)

# Calculate custom metrics
sharpe = qs.stats.sharpe(returns)
max_dd = qs.stats.max_drawdown(returns)
cagr = qs.stats.cagr(returns)

print(f"Sharpe: {sharpe:.2f}")
print(f"Max Drawdown: {max_dd:.2%}")
print(f"CAGR: {cagr:.2%}")
```

## 🛠️ Report Customization

QuantStats reports can be customized via environment variables or direct API calls:

```python
# Customize the report output
qs.reports.html(
    returns,
    output='my_report.html',
    title='Custom Title',
    benchmark=benchmark,
    download_filename='strategy_report.html',
    # Additional parameters
)
```

## 🔍 Troubleshooting

### Issue: "QuantStats not available"

**Solution:**
```bash
pip install quantstats
# or
pip install quantstats --upgrade
```

### Issue: Returns data looks wrong

**Solution:** Check that your backtest has sufficient data. QuantStats works best with:
- Minimum 1 year of data
- Daily or more frequent observations
- No extended gaps

### Issue: HTML report doesn't display

**Solution:**
- Check browser console for JavaScript errors
- Ensure output directory has write permissions
- Try opening in a different browser (Chrome/Firefox recommended)

## 📚 QuantStats Resources

- **Documentation**: https://github.com/ranaroussi/quantstats
- **Examples**: https://github.com/ranaroussi/quantstats/tree/main/examples
- **Metrics Reference**: https://github.com/ranaroussi/quantstats/blob/main/README.md#metrics

## 🎯 Best Practices

1. **Always generate HTML reports for final analysis** - They're more comprehensive than plots
2. **Use benchmarks** - Comparing to SPY/bonds helps contextualize performance
3. **Archive reports** - HTML files are self-contained; save them with your backtest configs
4. **Batch comparisons** - Use `--html` with batch_compare.py to analyze multiple strategies at once

## 💡 Example Workflow

```bash
# 1. Test a new strategy configuration
python run_yaml_backtest.py configs/my_new_strategy.yaml --html

# 2. Compare it against existing strategies
python batch_compare.py configs/my_new_strategy.yaml configs/baseline.yaml --html

# 3. Review HTML reports
open outputs/my_new_strategy_quantstats.html
open outputs/reports/*.html

# 4. If satisfied, archive the config and report
git add configs/my_new_strategy.yaml
git commit -m "Add new strategy configuration"
# Save HTML reports separately (they're in .gitignore)
```

---

**Happy analyzing! 📊**
