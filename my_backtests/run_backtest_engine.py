#!/usr/bin/env python3
"""
Refactored backtest engine for running YAML-configured backtests.

Usage:
    python run_backtest_engine.py <config_path>

Example:
    python run_backtest_engine.py configs/preliminary-possum.yaml

Outputs:
    - Portfolio performance metrics (pysystemtrade and QuantStats)
    - Equity curve and drawdown plot
    - HTML performance report (if QuantStats is available)
"""

import sys
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # ensure plotting works in headless environments

import matplotlib.pyplot as plt

# QuantStats setup with compatibility patches
try:
    import quantstats as qs  # type: ignore
    import quantstats.stats as qs_stats
    try:
        from quantstats import _compat as qs_compat
    except ImportError:  # pragma: no cover
        qs_compat = None

    if hasattr(qs_stats, "gain_to_pain_ratio"):
        _qs_original_gain_to_pain = qs_stats.gain_to_pain_ratio

        def _patched_gain_to_pain_ratio(returns, rf=0.0, resolution="M"):
            if resolution in {"ME", "MS"}:
                resolution = "M"
            elif resolution in {"QE", "QS"}:
                resolution = "Q"
            elif resolution in {"YE", "YS", "A"}:
                resolution = "Y"
            try:
                return _qs_original_gain_to_pain(returns, rf, resolution)
            except ValueError as err:
                if "Invalid frequency" in str(err) and resolution != "M":
                    return _qs_original_gain_to_pain(returns, rf, "M")
                raise

        qs_stats.gain_to_pain_ratio = _patched_gain_to_pain_ratio

    if qs_compat is not None and hasattr(qs_compat, "get_frequency_alias"):
        _qs_original_get_frequency_alias = qs_compat.get_frequency_alias

        def _patched_get_frequency_alias(freq: str) -> str:
            if freq in {"ME", "MS", "M"}:
                return "M"
            if freq in {"QE", "QS", "Q"}:
                return "Q"
            if freq in {"YE", "YS", "A", "Y"}:
                return "A"
            return _qs_original_get_frequency_alias(freq)

        qs_compat.get_frequency_alias = _patched_get_frequency_alias
except ImportError:  # pragma: no cover
    qs = None


def _to_scalar(value):
    """Convert QuantStats results to a float."""
    if value is None:
        return float("nan")
    # Direct float conversion works for numpy scalars and plain numbers
    try:
        return float(value)
    except (TypeError, ValueError):
        pass

    # Handle pandas objects
    if hasattr(value, "to_numpy"):
        arr = value.to_numpy().ravel()
        if arr.size:
            return float(arr[0])

    if hasattr(value, "squeeze"):
        squeezed = value.squeeze()
        if squeezed is not value:
            return _to_scalar(squeezed)

    if hasattr(value, "item"):
        try:
            return float(value.item())
        except (TypeError, ValueError):
            pass

    raise TypeError(f"Cannot convert value of type {type(value)} to scalar.")


# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_backtests.test_system import futures_system


def print_pysystemtrade_metrics(portfolio_curve):
    """Print all standard pysystemtrade portfolio accounting metrics."""
    print("\n" + "="*70)
    print("PYSYSTEMTRADE PORTFOLIO METRICS")
    print("="*70)

    # Return metrics
    print(f"\nAnnual Return:                {portfolio_curve.ann_mean():.2%}")
    print(f"Daily Mean Return:            {portfolio_curve.mean():.4%}")
    print(f"Annual Volatility:            {portfolio_curve.ann_std():.2%}")
    print(f"Daily Volatility:             {portfolio_curve.std():.4%}")

    # Risk-adjusted metrics
    print(f"\nSharpe Ratio:                 {portfolio_curve.sharpe():.2f}")
    print(f"Sortino Ratio:                {portfolio_curve.sortino():.2f}")
    print(f"Calmar Ratio:                 {portfolio_curve.calmar():.2f}")

    # Drawdown metrics
    print(f"\nWorst Drawdown:               {portfolio_curve.worst_drawdown():.2%}")
    print(f"Average Drawdown:             {portfolio_curve.avg_drawdown():.2%}")
    print(f"Avg Return to Drawdown:       {portfolio_curve.avg_return_to_drawdown():.2f}")
    print(f"Time in Drawdown:             {portfolio_curve.time_in_drawdown():.2%}")

    # Distribution metrics
    print(f"\nSkewness:                     {portfolio_curve.skew():.2f}")
    print(f"Min Daily Return:             {portfolio_curve.min():.2%}")
    print(f"Max Daily Return:             {portfolio_curve.max():.2%}")
    print(f"Median Daily Return:          {portfolio_curve.median():.4%}")

    # Win/Loss metrics
    print(f"\nAverage Gain:                 {portfolio_curve.avg_gain():.4%}")
    print(f"Average Loss:                 {portfolio_curve.avg_loss():.4%}")
    print(f"Gain to Loss Ratio:           {portfolio_curve.gaintolossratio():.2f}")
    print(f"Profit Factor:                {portfolio_curve.profitfactor():.2f}")
    print(f"Hit Rate:                     {portfolio_curve.hitrate():.2%}")

    # Statistical significance
    print(f"\nT-Statistic:                  {portfolio_curve.t_stat():.2f}")
    print(f"P-Value:                      {portfolio_curve.p_value():.4f}")

    print("\n" + "="*70)


def print_quantstats_metrics(daily_returns):
    """Print additional QuantStats metrics if available."""
    if qs is None:
        return

    print("\n" + "="*70)
    print("QUANTSTATS ADDITIONAL METRICS")
    print("="*70)

    try:
        print(f"\nCAGR:                         {_to_scalar(qs.stats.cagr(daily_returns)):.2%}")
        print(f"Volatility (annual):          {_to_scalar(qs.stats.volatility(daily_returns)):.2%}")
        print(f"Max Drawdown:                 {_to_scalar(qs.stats.max_drawdown(daily_returns)):.2%}")
        print(f"Best Day:                     {_to_scalar(qs.stats.best(daily_returns)):.2%}")
        print(f"Worst Day:                    {_to_scalar(qs.stats.worst(daily_returns)):.2%}")
        print(f"Avg Win:                      {_to_scalar(qs.stats.avg_win(daily_returns)):.2%}")
        print(f"Avg Loss:                     {_to_scalar(qs.stats.avg_loss(daily_returns)):.2%}")
        print(f"Win Rate:                     {_to_scalar(qs.stats.win_rate(daily_returns)):.2%}")
        print(f"Value at Risk (95%):          {_to_scalar(qs.stats.value_at_risk(daily_returns)):.2%}")
        print(f"Conditional VaR (95%):        {_to_scalar(qs.stats.cvar(daily_returns)):.2%}")
    except Exception as e:
        print(f"Note: Some QuantStats metrics could not be calculated: {e}")

    print("\n" + "="*70)


def run_backtest(config_path: str):
    """
    Run a backtest using the specified config file.

    Args:
        config_path: Path to the YAML configuration file (relative or absolute)
    """
    # Resolve config path
    config_file = Path(config_path)
    if not config_file.is_absolute():
        # Try relative to current directory first
        if config_file.exists():
            config_file = config_file.resolve()
        else:
            # Try relative to my_backtests directory
            config_file = (PROJECT_ROOT / "my_backtests" / config_path).resolve()

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    print(f"\n{'='*70}")
    print(f"Running backtest with config: {config_file}")
    print(f"{'='*70}\n")

    # Build the system
    system = futures_system(config_filename=str(config_file))

    # Get portfolio performance
    portfolio = system.accounts.portfolio()
    percent_portfolio = portfolio.percent

    # Convert to daily returns for QuantStats
    daily_returns = percent_portfolio.as_ts.dropna() / 100.0

    if daily_returns.empty:
        raise RuntimeError("No daily returns available to compute performance metrics.")

    # Print all pysystemtrade metrics
    print_pysystemtrade_metrics(percent_portfolio)

    # Print QuantStats metrics if available
    if qs is not None:
        print_quantstats_metrics(daily_returns)

    # Prepare equity curve and drawdown for plotting
    equity_index = (1.0 + daily_returns).cumprod()
    equity_curve = (equity_index - 1.0) * 100.0
    drawdown_curve = (equity_index / equity_index.cummax() - 1.0) * 100.0

    # Create output directory
    output_dir = PROJECT_ROOT / "my_backtests" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename from config
    config_name = config_file.stem

    # Generate QuantStats HTML report if available
    if qs is not None:
        qs.extend_pandas()
        report_path = output_dir / f"{config_name}_report.html"
        try:
            qs.reports.html(
                daily_returns,
                output=str(report_path),
                title=f"{config_name} Backtest",
                display=False,
            )
            print(f"\nQuantStats HTML report saved to: {report_path}")
        except Exception as e:
            print(f"\nNote: Could not generate QuantStats report: {e}")

    # Create equity curve and drawdown plot
    fig, (ax_eq, ax_dd) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))

    equity_curve.plot(ax=ax_eq, color="steelblue", linewidth=1.2)
    ax_eq.set_title(f"{config_name} – Equity Curve")
    ax_eq.set_ylabel("Cumulative Return (%)")
    ax_eq.grid(True, alpha=0.3)

    drawdown_curve.plot(ax=ax_dd, color="firebrick", linewidth=1.2)
    ax_dd.set_title(f"{config_name} – Drawdown")
    ax_dd.set_ylabel("Drawdown (%)")
    ax_dd.set_xlabel("Date")
    ax_dd.grid(True, alpha=0.3)

    fig.tight_layout()
    plot_path = output_dir / f"{config_name}_equity.png"
    fig.savefig(plot_path, dpi=150)

    print(f"Equity curve plot saved to: {plot_path}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Run a backtest using a YAML configuration file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_backtest_engine.py configs/preliminary-possum.yaml
  python run_backtest_engine.py /absolute/path/to/config.yaml
        """
    )
    parser.add_argument(
        "config",
        type=str,
        help="Path to the YAML config file (relative or absolute)"
    )

    args = parser.parse_args()

    try:
        run_backtest(args.config)
    except Exception as e:
        print(f"\nError running backtest: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
