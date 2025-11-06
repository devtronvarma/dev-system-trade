#!/usr/bin/env python3
"""
Run the preliminary possum backtest and produce headline diagnostics.

Outputs:
    - Equity curve and drawdown plot written to my_backtests/outputs/
    - Annual return, max drawdown, and Sharpe ratio printed to stdout
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # ensure plotting works in headless environments

import matplotlib.pyplot as plt

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

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_backtests.test_system import futures_system


def run_backtest():
    config_path = (PROJECT_ROOT / "my_backtests" / "configs" / "preliminary-possum.yaml").resolve()

    system = futures_system(config_filename=str(config_path))

    portfolio = system.accounts.portfolio()
    percent_portfolio = portfolio.percent

    daily_returns = percent_portfolio.as_ts.dropna() / 100.0

    if daily_returns.empty:
        raise RuntimeError("No daily returns available to compute performance metrics.")

    equity_index = (1.0 + daily_returns).cumprod()
    equity_curve = (equity_index - 1.0) * 100.0
    drawdown_curve = (equity_index / equity_index.cummax() - 1.0) * 100.0

    output_dir = PROJECT_ROOT / "my_backtests" / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    if qs is not None:
        qs.extend_pandas()
        report_path = output_dir / "preliminary_possum_report.html"
        qs.reports.html(
            daily_returns,
            output=str(report_path),
            title="Preliminary Possum Backtest",
            display=False,
        )
        ann_return = _to_scalar(qs.stats.cagr(daily_returns))
        sharpe = _to_scalar(qs.stats.sharpe(daily_returns))
        max_drawdown = _to_scalar(qs.stats.max_drawdown(daily_returns))
        report_msg = f"QuantStats report saved to {report_path}"
    else:
        ann_return = percent_portfolio.ann_mean()
        sharpe = percent_portfolio.sharpe()
        max_drawdown = percent_portfolio.worst_drawdown()
        report_msg = "QuantStats not installed; skipped HTML report."

    fig, (ax_eq, ax_dd) = plt.subplots(2, 1, sharex=True, figsize=(12, 8))
    equity_curve.plot(ax=ax_eq, color="steelblue", linewidth=1.2)
    ax_eq.set_title("Preliminary Possum – Equity Curve")
    ax_eq.set_ylabel("Cumulative Return (%)")

    drawdown_curve.plot(ax=ax_dd, color="firebrick", linewidth=1.2)
    ax_dd.set_title("Preliminary Possum – Drawdown")
    ax_dd.set_ylabel("Drawdown (%)")
    ax_dd.set_xlabel("Date")

    fig.tight_layout()
    plot_path = output_dir / "preliminary_possum_equity.png"
    fig.savefig(plot_path, dpi=150)

    print(f"Annual Return: {ann_return:.2%}")
    print(f"Max Drawdown: {max_drawdown:.2%}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Plot saved to {plot_path}")
    print(report_msg)


if __name__ == "__main__":
    run_backtest()
